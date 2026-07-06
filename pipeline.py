import csv
import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel

from db import create_tables, get_engine, set_metadata, upsert
from extractors.extractors import ENDPOINT_CONFIGS

START_YEAR = 2022
RAW_DIR = Path("data/raw")
FAILED_REQUESTS_FILE = Path("data/failed_requests.csv")
BASE_HOST = "https://transparencia.porciuncula.rj.gov.br"

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


def _insert_entities(engine: Engine, entities: dict[int, str]) -> None:
    table = SQLModel.metadata.tables["empresas"]
    with engine.connect() as conn:
        for eid, ename in entities.items():
            stmt = pg_insert(table).values(id=eid, nome=ename).on_conflict_do_nothing()
            conn.execute(stmt)
        conn.commit()


class DatabaseLoader:
    """Manages loading standard schemas and raw JSON datasets into the PostgreSQL database."""

    @staticmethod
    def get_entities(engine: Engine) -> dict[int, str]:
        """Retrieves mapped corporate/fund entities from the database."""
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id, nome FROM empresas")).fetchall()
        return {row[0]: row[1] for row in rows}

    @classmethod
    def load_from_dir(cls, dir_path: str | None) -> None:
        """Loads extracted JSON files from a specific raw run directory into the database."""
        if not dir_path:
            run_dirs = list(Path("data/raw_runs").iterdir())
            if not run_dirs:
                raise ValueError("No raw run directories found under data/raw_runs")
            dir_path = str(max(run_dirs, key=lambda d: d.stat().st_mtime))

        run_dir = Path(dir_path)
        if not run_dir.exists():
            raise ValueError(f"Directory {dir_path} does not exist.")

        engine = get_engine()
        create_tables(engine)

        try:
            extraction_dt = datetime.strptime(run_dir.name, "%Y%m%d_%H%M%S")
            extraction_date = extraction_dt.isoformat(sep=" ")
        except ValueError:
            extraction_date = None

        for json_file in run_dir.rglob("*.json"):
            table = json_file.parent.name
            config = next((c for c in ENDPOINT_CONFIGS if c[2] == table), None)
            if not config:
                logger.warning("Could not find config for table: %s", table)
                continue

            key_cols = cast(list[str], list(config[3]))  # type: ignore
            post_process = config[6] if len(config) > 6 else None

            parts = json_file.stem.split("_")
            empresa_id = parts[0]
            year = int(parts[1])

            rows = json.loads(json_file.read_text(encoding="utf-8"))
            normalised = PipelineHelper.normalize(rows, year, str(empresa_id), post_process)
            count = upsert(engine, table, normalised, key_cols)  # type: ignore
            logger.info("Loaded %s / %s / %d → %d rows", table, empresa_id, year, count)

        if extraction_date:
            set_metadata(engine, "last_extracted_at", extraction_date)
            logger.info("Set extraction date: %s", extraction_date)

        logger.info("Loading complete.")


class DataExtractor:
    """Handles communicating with portal APIs to pull down raw JSON datasets."""

    @staticmethod
    def log_failed_request(
        listagem: str, empresa_name: str, year: int, error: Any, run_dir: Path | None = None
    ) -> None:
        """Persistently logs extraction errors to the failed requests ledger."""
        log_file = run_dir / "failed_requests.csv" if run_dir else FAILED_REQUESTS_FILE
        file_exists = log_file.exists()
        with open(log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "listagem", "empresa", "year", "error"])
            writer.writerow([datetime.now().isoformat(), listagem, empresa_name, year, str(error)])

    @staticmethod
    def get_extractor(path, listagem, table, key_cols, extra, post_process, extractor_cls):
        """Constructs an isolated API extractor client instance."""
        return extractor_cls(path, listagem, table, key_cols, extra, post_process)

    @classmethod
    def extract_only(cls, years: list[int] | None = None, only: str | None = None) -> None:
        """Extracts data from portal endpoints and saves raw outputs into a timestamped directory."""
        if years is None:
            years = list(range(START_YEAR, date.today().year + 1))

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(f"data/raw_runs/{timestamp}")
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Saving raw data to %s", run_dir)

        engine = get_engine()
        entities = DatabaseLoader.get_entities(engine)

        endpoints = ENDPOINT_CONFIGS
        if only:
            valid = [e[1] for e in ENDPOINT_CONFIGS]
            if only not in valid:
                raise ValueError(f"Unknown listagem: {only!r}")
            endpoints = [e for e in ENDPOINT_CONFIGS if e[1] == only]

        for config_tuple in cast(list[Any], endpoints):
            config_list = cast(list[Any], list(cast(list[Any], config_tuple)))
            path = str(config_list[0])
            listagem = str(config_list[1])
            table = str(config_list[2])
            extractor_cls = config_list[5]

            extra = cast(dict[str, str], dict(config_list[4]))
            extractor = cls.get_extractor(path, listagem, table, [], extra, None, extractor_cls)

            for empresa_id, empresa_name in entities.items():
                for year in years:
                    try:
                        rows = extractor.extract(empresa_id, year)
                        run_file = run_dir / table / f"{empresa_id}_{year}.json"
                        run_file.parent.mkdir(parents=True, exist_ok=True)
                        run_file.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
                        logger.info("Extracted %s / %s / %d to %s", listagem, empresa_name, year, run_file)
                    except Exception as exc:
                        logger.warning("Failed extraction %s / %s / %d: %s", listagem, empresa_name, year, exc)
                        cls.log_failed_request(listagem, empresa_name, year, exc, run_dir=run_dir)

        logger.info("Extraction complete. Data saved in %s", run_dir)


class PipelineRunner:
    """Orchestrates standard execution loops across all extraction and loading routines."""

    @classmethod
    def run(
        cls,
        years: list[int] | None = None,
        start_from: str | None = None,
        only: str | None = None,
        retry_failed: bool = False,
        raw_only: bool = False,
    ) -> None:
        """Main execution sequence linking the scraping interfaces to the database layer."""
        if years is None:
            years = list(range(START_YEAR, date.today().year + 1))

        engine = get_engine()
        create_tables(engine)

        _insert_entities(
            engine,
            {
                10: "FUNDO DE SOLIDARIEDADE - FUNDESOL",
                3: "FUNDO MUNICIPAL DE ASSISTENCIA SOCIAL",
                9: "FUNDO MUNICIPAL DE DEFESA AMBIENTAL",
                8: "FUNDO MUNICIPAL DE EDUCAÇÃO",
                2: "FUNDO MUNICIPAL DE SAUDE",
                7: "PREFEITURA MUNICIPAL DE PORCIÚNCULA",
            },
        )

        valid = [e[1] for e in ENDPOINT_CONFIGS]

        if retry_failed:
            if not FAILED_REQUESTS_FILE.exists():
                logger.info("No failed requests log found to retry.")
                return

            with open(FAILED_REQUESTS_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                failed_tasks = list(reader)

            FAILED_REQUESTS_FILE.unlink()
            entity_name_to_id = {v: k for k, v in DatabaseLoader.get_entities(engine).items()}

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_dir = Path(f"data/raw_runs/{timestamp}")
            run_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Saving raw retry data to %s", run_dir)

            for task in failed_tasks:
                config = next((c for c in ENDPOINT_CONFIGS if c[1] == task["listagem"]), None)
                if not config:
                    logger.warning("Could not find config for listagem: %s", task["listagem"])
                    continue

                empresa_id = entity_name_to_id.get(task["empresa"])
                if not empresa_id:
                    logger.warning("Could not find ID for empresa: %s", task["empresa"])
                    continue

                raw_data = config
                if raw_data is None:
                    continue
                config_list = cast(list[Any], list(cast(list[Any], raw_data)))
                path, listagem, table, key_cols, extra, extractor_cls, *post_process = cast(list[Any], config_list)  # type: ignore
                post_process = post_process[0] if post_process else None  # type: ignore
                extractor = DataExtractor.get_extractor(
                    path, listagem, table, key_cols, extra, post_process, extractor_cls
                )

                try:
                    rows = extractor.extract(empresa_id, int(task["year"]))
                    raw_path = run_dir / str(table) / f"{empresa_id}_{task['year']}.json"
                    raw_path.parent.mkdir(parents=True, exist_ok=True)
                    raw_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
                    normalised = PipelineHelper.normalize(rows, int(task["year"]), str(empresa_id), post_process)
                    count = upsert(engine, str(table), normalised, key_cols)  # type: ignore
                    logger.info(
                        "Retry successful: %s / %s / %s → %d rows", listagem, task["empresa"], task["year"], count
                    )
                except Exception as exc:
                    logger.warning("Retry FAILED: %s / %s / %s: %s", listagem, task["empresa"], task["year"], exc)
                    DataExtractor.log_failed_request(listagem, task["empresa"], int(task["year"]), exc, run_dir=run_dir)
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(f"data/raw_runs/{timestamp}")
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Saving raw data to %s", run_dir)

        endpoints = ENDPOINT_CONFIGS
        if only:
            if only not in valid:
                raise ValueError(f"Unknown listagem: {only!r}. Valid values: {valid}")
            endpoints = [e for e in ENDPOINT_CONFIGS if e[1] == only]
        if start_from:
            if start_from not in valid:
                raise ValueError(f"Unknown listagem: {start_from!r}. Valid values: {valid}")
            idx = next(i for i, e in enumerate(ENDPOINT_CONFIGS) if e[1] == start_from)
            endpoints = ENDPOINT_CONFIGS[idx:]

        entities = DatabaseLoader.get_entities(engine)
        total = sum(len(entities) * len(years) for _ in endpoints)
        done = 0

        for config_tuple in cast(list[Any], endpoints):
            config_list = cast(list[Any], list(cast(list[Any], config_tuple)))
            path = str(config_list[0])
            listagem = str(config_list[1])
            table = str(config_list[2])
            key_cols = cast(list[str], list(config_list[3]))
            extra = cast(dict[str, str], dict(config_list[4]))
            extractor_cls = config_list[5]
            post_process = config_list[6] if len(config_list) > 6 else None  # type: ignore

            extractor = DataExtractor.get_extractor(path, listagem, table, key_cols, extra, post_process, extractor_cls)

            entities = DatabaseLoader.get_entities(engine)
            for empresa_id, empresa_name in entities.items():
                for year in years:
                    raw_path = run_dir / str(table) / f"{empresa_id}_{year}.json"
                    try:
                        if raw_only:
                            if not raw_path.exists():
                                logger.info("Skipping %s / %s / %d (raw file not found)", listagem, empresa_name, year)
                                done += 1
                                continue
                            rows = json.loads(raw_path.read_text(encoding="utf-8"))
                        else:
                            rows = extractor.extract(empresa_id, year)
                            raw_path.parent.mkdir(parents=True, exist_ok=True)
                            raw_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2))

                        normalised = PipelineHelper.normalize(rows, year, str(empresa_id), post_process)
                        count = upsert(engine, str(table), normalised, key_cols)  # type: ignore
                        logger.info(
                            "[%d/%d] %s / %s / %d → %d rows", done + 1, total, listagem, empresa_name, year, count
                        )
                    except Exception as exc:
                        logger.warning("SKIP %s / %s / %d: %s", listagem, empresa_name, year, exc)
                        DataExtractor.log_failed_request(listagem, empresa_name, year, exc, run_dir=run_dir)
                    done += 1

        set_metadata(engine, "last_extracted_at", datetime.now().isoformat(sep=" ", timespec="seconds"))
        logger.info("Pipeline complete.")


def run(
    years: list[int] | None = None,
    start_from: str | None = None,
    only: str | None = None,
    retry_failed: bool = False,
    raw_only: bool = False,
) -> None:
    """Standard orchestrator runner wrapper for downstream backwards compatibility."""
    PipelineRunner.run(years, start_from, only, retry_failed, raw_only)


def extract_only(years: list[int] | None = None, only: str | None = None) -> None:
    """Isolated raw extraction routine wrapper."""
    DataExtractor.extract_only(years, only)


def load_from_dir(dir_path: str | None) -> None:
    """Directory loading database upsert routine wrapper."""
    DatabaseLoader.load_from_dir(dir_path)


if __name__ == "__main__":
    run()
