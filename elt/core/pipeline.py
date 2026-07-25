import csv
import importlib
import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import cast

from elt.core.config import PortalConfig
from elt.core.db import create_tables, get_engine, set_metadata, upsert
from elt.extract.base import EndpointConfig

_portal = PortalConfig.load()
_extractor_module = importlib.import_module(f"elt.extract.{_portal.slug}.api_endpoints")
ENDPOINT_CONFIGS: list[EndpointConfig] = _extractor_module.ENDPOINT_CONFIGS
START_YEAR = _portal.ano_inicial
BASE_HOST = _portal.base_host
RAW_DIR = Path("data/raw")
FAILED_REQUESTS_FILE = Path("data/failed_requests.csv")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_MONTH_MAP = {
    "Janeiro": "01",
    "Fevereiro": "02",
    "Março": "03",
    "Abril": "04",
    "Maio": "05",
    "Junho": "06",
    "Julho": "07",
    "Agosto": "08",
    "Setembro": "09",
    "Outubro": "10",
    "Novembro": "11",
    "Dezembro": "12",
}


class PipelineHelper:
    """Helper methods for data processing, sanitization, and normalization."""

    @staticmethod
    def sanitize_key(k: str) -> str:
        """Sanitizes raw API keys into standardized, snake_case strings."""
        return re.sub(r"[^a-z0-9]+", "_", k.lower()).strip("_")

    @staticmethod
    def extract_month(row: dict) -> str | None:
        """Attempts to parse and extract a standardized two-digit month string from a data row."""
        for field in ["dtassi", "datae", "dtpublic", "dataadmissao"]:
            if field in row and row[field]:
                try:
                    return datetime.strptime(row[field], "%d/%m/%Y %H:%M:%S").strftime("%m")
                except ValueError:
                    continue

        if "referencia_nome" in row and row["referencia_nome"]:
            parts = row["referencia_nome"].split(" - ")
            if len(parts) > 1:
                mes = parts[1].strip()
                return _MONTH_MAP.get(mes)

        return None

    @classmethod
    def normalize(cls, rows: list[dict], ano: int, empresa: str, post_process=None) -> list[dict]:
        """Normalizes and standardizes lists of raw dictionary rows."""
        out = []
        for r in rows:
            normalised = {cls.sanitize_key(k): v for k, v in r.items()}
            if not normalised.get("ano"):
                normalised["ano"] = ano
            normalised.setdefault("empresa", empresa)
            raw_ano = int(normalised["ano"])
            if raw_ano < 100:
                normalised["ano"] = 2000 + raw_ano
            if post_process:
                normalised = post_process(normalised)

            mes = cls.extract_month(normalised)
            if mes:
                normalised["mes"] = mes

            out.append(normalised)
        return out


class DataExtractor:
    """Handles logic for fetching, running, logging and extracting endpoints."""

    @classmethod
    def get_extractor(
        cls,
        base_path: str,
        listagem: str,
        table: str,
        key_cols: list[str],
        extra: dict,
        post_process,
        extractor_cls,
        base_url: str = "",
    ):
        return extractor_cls(
            base_path=base_path,
            listagem=listagem,
            table=table,
            key_cols=key_cols,
            extra=extra,
            post_process=post_process,
            base_url=base_url or BASE_HOST,
        )

    @classmethod
    def log_failed_request(
        cls, listagem: str, empresa: str, year: int, exc: Exception, run_dir: Path | None = None
    ) -> None:
        """Logs failed endpoints to both stdout and structured CSV log files."""
        write_header = not FAILED_REQUESTS_FILE.exists()
        with open(FAILED_REQUESTS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "listagem", "empresa", "year", "error"])
            if write_header:
                writer.writeheader()
            writer.writerow(
                {
                    "timestamp": datetime.now().isoformat(),
                    "listagem": listagem,
                    "empresa": empresa,
                    "year": year,
                    "error": str(exc),
                }
            )

        if run_dir:
            run_failed_log = run_dir / "failed_requests.csv"
            write_run_header = not run_failed_log.exists()
            with open(run_failed_log, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "listagem", "empresa", "year", "error"])
                if write_run_header:
                    writer.writeheader()
                writer.writerow(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "listagem": listagem,
                        "empresa": empresa,
                        "year": year,
                        "error": str(exc),
                    }
                )

    @classmethod
    def extract_only(cls, years: list[int] | None = None, only: str | None = None) -> None:
        """Performs raw data extraction into timestamped directories without loading database schemas."""
        if years is None:
            years = list(range(START_YEAR, date.today().year + 1))

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(f"data/raw_runs/{timestamp}")
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Saving raw data to %s (extraction only)", run_dir)

        endpoints = ENDPOINT_CONFIGS
        if only:
            valid = [e.listagem for e in ENDPOINT_CONFIGS]
            if only not in valid:
                raise ValueError(f"Unknown listagem: {only!r}. Valid values: {valid}")
            endpoints = [e for e in ENDPOINT_CONFIGS if e.listagem == only]

        entities = _portal.load_orgaos()
        total = len(endpoints) * len(entities) * len(years)
        done = 0

        for config in cast(list[EndpointConfig], endpoints):
            listagem = config.listagem
            table = config.table
            extractor = cls.get_extractor(
                config.base_path,
                config.listagem,
                config.table,
                config.key_cols,
                config.extra,
                config.post_process,
                config.extractor_cls,
                base_url=config.base_url,
            )

            for empresa_id, nome_empresa in entities.items():
                for year in years:
                    raw_path = run_dir / str(table) / f"{empresa_id}_{year}.json"
                    try:
                        rows = extractor.extract(empresa_id, year)
                        raw_path.parent.mkdir(parents=True, exist_ok=True)
                        raw_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
                        logger.info(
                            "[%d/%d] Extracted %s / %s / %d → %d rows",
                            done + 1,
                            total,
                            listagem,
                            nome_empresa,
                            year,
                            len(rows),
                        )
                    except Exception as exc:
                        logger.warning("SKIP %s / %s / %d: %s", listagem, nome_empresa, year, exc)
                        cls.log_failed_request(listagem, nome_empresa, year, exc, run_dir=run_dir)
                    done += 1

        meta_file = run_dir / "metadata.json"
        meta_file.write_text(
            json.dumps({"extracted_at": datetime.now().isoformat(sep=" ", timespec="seconds")}, indent=2)
        )
        logger.info("Extraction complete. Raw files written to %s", run_dir)


class DatabaseLoader:
    """Manages loading standard schemas and raw JSON datasets into the PostgreSQL database."""

    @classmethod
    def load_from_dir(cls, dir_path: str | None) -> None:
        """Loads extracted JSON files from a specific raw run directory into the database."""
        if not dir_path:
            run_dirs = list(Path("data/raw_runs").iterdir())
            if not run_dirs:
                raise ValueError("No raw run directories found under data/raw_runs")
            dir_path = str(max(run_dirs, key=lambda d: d.stat().st_mtime))

        p = Path(dir_path)
        logger.info("Loading extracted JSON files from %s...", p)
        engine = get_engine()
        create_tables(engine)

        portal_slug = p.name.split("_")[0] if "_" in p.name else _portal.slug
        total_inserted = 0
        for cfg in ENDPOINT_CONFIGS:
            file_path = p / f"{cfg.table}.json"
            if not file_path.exists():
                logger.warning("File %s.json not found under %s — skipping", cfg.table, p)
                continue

            try:
                rows = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error("Failed to read %s: %s", file_path, e)
                continue

            if not rows:
                continue

            n = upsert(engine, cfg.table, rows, cfg.key_cols)
            logger.info("Loaded %d rows into %s", n, cfg.table)
            total_inserted += n

        metadata_file = p / "metadata.json"
        if metadata_file.exists():
            meta = json.loads(metadata_file.read_text(encoding="utf-8"))
            if "extracted_at" in meta:
                set_metadata(engine, "last_extracted_at", meta["extracted_at"], portal_slug)

        logger.info("Database load complete. Total rows inserted/updated: %d", total_inserted)


class PipelineRunner:
    """Orchestrates pipeline execution sequences."""

    @classmethod
    def run(
        cls,
        years: list[int] | None = None,
        start_from: str | None = None,
        only: str | None = None,
        _retry_failed: bool = False,
        raw_only: bool = False,
    ) -> None:
        """Main execution sequence linking scraping interfaces to the database layer."""
        if years is None:
            years = list(range(START_YEAR, date.today().year + 1))

        engine = get_engine()
        create_tables(engine)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(f"data/raw_runs/{timestamp}")
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Saving raw data to %s", run_dir)

        endpoints = ENDPOINT_CONFIGS
        if only:
            valid = [e.listagem for e in ENDPOINT_CONFIGS]
            if only not in valid:
                raise ValueError(f"Unknown listagem: {only!r}. Valid values: {valid}")
            endpoints = [e for e in ENDPOINT_CONFIGS if e.listagem == only]
        if start_from:
            valid = [e.listagem for e in ENDPOINT_CONFIGS]
            if start_from not in valid:
                raise ValueError(f"Unknown listagem: {start_from!r}. Valid values: {valid}")
            idx = next(i for i, e in enumerate(ENDPOINT_CONFIGS) if e.listagem == start_from)
            endpoints = ENDPOINT_CONFIGS[idx:]

        entities = _portal.load_orgaos()
        total = sum(len(entities) * len(years) for _ in endpoints)
        done = 0

        for config in cast(list[EndpointConfig], endpoints):
            listagem = config.listagem
            table = config.table
            extractor = DataExtractor.get_extractor(
                config.base_path,
                config.listagem,
                config.table,
                config.key_cols,
                config.extra,
                config.post_process,
                config.extractor_cls,
                base_url=config.base_url,
            )

            for empresa_id, nome_empresa in entities.items():
                for year in years:
                    raw_path = run_dir / str(table) / f"{empresa_id}_{year}.json"
                    try:
                        if raw_only:
                            if not raw_path.exists():
                                logger.info("Skipping %s / %s / %d (raw file not found)", listagem, nome_empresa, year)
                                done += 1
                                continue
                            rows = json.loads(raw_path.read_text(encoding="utf-8"))
                        else:
                            rows = extractor.extract(empresa_id, year)
                            raw_path.parent.mkdir(parents=True, exist_ok=True)
                            raw_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2))

                        normalised = PipelineHelper.normalize(rows, year, empresa_id, config.post_process)
                        target_table_for_upsert = (
                            "despesas_por_exigibilidade"
                            if "despesas_por_exigibilidade" in config.table
                            else str(config.table)
                        )

                        count = upsert(engine, target_table_for_upsert, normalised, config.key_cols)
                        logger.info(
                            "[%d/%d] %s / %s / %d → %d rows",
                            done + 1,
                            total,
                            config.listagem,
                            nome_empresa,
                            year,
                            count,
                        )
                    except Exception as exc:
                        logger.warning("SKIP %s / %s / %d: %s", listagem, nome_empresa, year, exc)
                        DataExtractor.log_failed_request(listagem, nome_empresa, year, exc, run_dir=run_dir)
                    done += 1

        set_metadata(engine, "last_extracted_at", datetime.now().isoformat(sep=" ", timespec="seconds"), _portal.slug)
        logger.info("Pipeline complete.")


def run(
    years: list[int] | None = None,
    start_from: str | None = None,
    only: str | None = None,
    retry_failed: bool = False,
    raw_only: bool = False,
) -> None:
    PipelineRunner.run(years, start_from, only, retry_failed, raw_only)


def extract_only(years: list[int] | None = None, only: str | None = None) -> None:
    DataExtractor.extract_only(years, only)


def load_from_dir(dir_path: str | None = None) -> None:
    DatabaseLoader.load_from_dir(dir_path)
