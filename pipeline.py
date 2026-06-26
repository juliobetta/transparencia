import csv
import json
import logging
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

from db import create_tables, get_connection, set_metadata, upsert
from extractors.extractors import ENDPOINT_CONFIGS

FAILED_REQUESTS_FILE = Path("data/failed_requests.csv")


def _log_failed_request(listagem, empresa_name, year, error):
    file_exists = FAILED_REQUESTS_FILE.exists()
    with open(FAILED_REQUESTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "listagem", "empresa", "year", "error"])
        writer.writerow([datetime.now().isoformat(), listagem, empresa_name, year, str(error)])


def _get_extractor(path, listagem, table, key_cols, extra, post_process, extractor_cls):
    return extractor_cls(path, listagem, table, key_cols, extra, post_process)


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


def _extract_month(row: dict) -> str | None:
    # Check date fields
    for field in ["dtassi", "datae", "dtpublic", "dataadmissao"]:
        if field in row and row[field]:
            try:
                return datetime.strptime(row[field], "%d/%m/%Y %H:%M:%S").strftime("%m")
            except ValueError:
                continue

    # Check reference name
    if "referencia_nome" in row and row["referencia_nome"]:
        # Format: "Folha Mensal - Dezembro"
        parts = row["referencia_nome"].split(" - ")
        if len(parts) > 1:
            mes = parts[1].strip()
            return _MONTH_MAP.get(mes)

    return None


RAW_DIR = Path("data/raw")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_HOST = "https://transparencia.porciuncula.rj.gov.br"


def _get_entities(conn: sqlite3.Connection) -> dict:
    rows = conn.execute("SELECT id, nome FROM empresas").fetchall()
    return {row["id"]: row["nome"] for row in rows}


def _post_process_contratos(row: dict) -> dict:
    # Raw field is CODIGO (e.g. "0053/26"), not NUMERO — map it to the key column
    row.setdefault("numero", row.get("codigo", ""))
    # PROCLIC format is "000120/26" — strip the /YY suffix to match licitacoes.numero
    proclic = row.get("proclic", "")
    row["licitacao_numero"] = proclic.split("/")[0] if proclic else ""
    return row


START_YEAR = 2022


def _sanitize_key(k: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", k.lower()).strip("_")


def _normalize(rows: list[dict], ano: int, empresa: str, post_process=None) -> list[dict]:
    out = []
    for r in rows:
        normalised = {_sanitize_key(k): v for k, v in r.items()}
        if not normalised.get("ano"):
            normalised["ano"] = ano
        normalised.setdefault("empresa", empresa)
        raw_ano = int(normalised["ano"])
        if raw_ano < 100:
            normalised["ano"] = 2000 + raw_ano
        if post_process:
            normalised = post_process(normalised)

        # Add month extraction
        mes = _extract_month(normalised)
        if mes:
            normalised["mes"] = mes

        out.append(normalised)
    return out


def run(
    years: list[int] | None = None,
    start_from: str | None = None,
    only: str | None = None,
    retry_failed: bool = False,
    raw_only: bool = False,
) -> None:
    if years is None:
        years = list(range(START_YEAR, date.today().year + 1))

    conn = get_connection()
    create_tables(conn)
    # Ensure entities are populated
    for eid, ename in {
        10: "FUNDO DE SOLIDARIEDADE - FUNDESOL",
        3: "FUNDO MUNICIPAL DE ASSISTENCIA SOCIAL",
        9: "FUNDO MUNICIPAL DE DEFESA AMBIENTAL",
        8: "FUNDO MUNICIPAL DE EDUCAÇÃO",
        2: "FUNDO MUNICIPAL DE SAUDE",
        7: "PREFEITURA MUNICIPAL DE PORCIÚNCULA",
    }.items():
        conn.execute("INSERT OR IGNORE INTO empresas (id, nome) VALUES (?, ?)", (eid, ename))
    conn.commit()

    valid = [e[1] for e in ENDPOINT_CONFIGS]

    if retry_failed:
        if not FAILED_REQUESTS_FILE.exists():
            logger.info("No failed requests log found to retry.")
            return

        with open(FAILED_REQUESTS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            failed_tasks = list(reader)

        # Clear log before retrying to repopulate if they fail again
        FAILED_REQUESTS_FILE.unlink()

        entity_name_to_id = {v: k for k, v in _get_entities(conn).items()}

        for task in failed_tasks:
            config = next((c for c in ENDPOINT_CONFIGS if c[1] == task["listagem"]), None)
            if not config:
                logger.warning("Could not find config for listagem: %s", task["listagem"])
                continue

            empresa_id = entity_name_to_id.get(task["empresa"])
            if not empresa_id:
                logger.warning("Could not find ID for empresa: %s", task["empresa"])
                continue

            # Type cast for retry loop
            raw_data = config
            if raw_data is None:
                continue
            config_list: list[Any] = cast(list[Any], list(cast(list[Any], raw_data)))  # type: ignore
            # Type ignore for unpacking
            path, listagem, table, key_cols, extra, extractor_cls, *post_process = cast(list[Any], config_list)  # type: ignore
            post_process = post_process[0] if post_process else None  # type: ignore
            extractor = _get_extractor(path, listagem, table, key_cols, extra, post_process, extractor_cls)

            try:
                # Type cast for retry loop
                rows = extractor.extract(empresa_id, int(task["year"]))
                raw_path = RAW_DIR / str(table) / f"{empresa_id}_{task['year']}.json"
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
                normalised = _normalize(rows, int(task["year"]), str(empresa_id), post_process)
                count = upsert(conn, str(table), normalised, key_cols)  # type: ignore
                logger.info("Retry successful: %s / %s / %s → %d rows", listagem, task["empresa"], task["year"], count)
            except Exception as exc:
                logger.warning("Retry FAILED: %s / %s / %s: %s", listagem, task["empresa"], task["year"], exc)
                _log_failed_request(listagem, task["empresa"], task["year"], exc)
        return

    endpoints = ENDPOINT_CONFIGS
    if only:
        if only not in valid:
            raise ValueError(f"Unknown listagem: {only!r}. Valid values: {valid}")
        endpoints = [e for e in ENDPOINT_CONFIGS if e[1] == only]
    if start_from:
        if start_from not in valid:
            raise ValueError(f"Unknown listagem: {start_from!r}. Valid values: {valid}")
        # Find index and update endpoints
        idx = next(i for i, e in enumerate(ENDPOINT_CONFIGS) if e[1] == start_from)
        endpoints = ENDPOINT_CONFIGS[idx:]

    # Total needs to be calculated dynamically
    entities = _get_entities(conn)
    total = sum(len(entities) * len(years) for _ in endpoints)
    done = 0

    for config_tuple in cast(list[Any], endpoints):
        # Force type casting for list and dict
        config_list: list[Any] = cast(list[Any], list(cast(list[Any], config_tuple)))  # type: ignore
        path = str(config_list[0])
        listagem = str(config_list[1])
        table = str(config_list[2])
        # Force type casting for list and dict
        key_cols = cast(list[str], list(config_list[3]))
        extra = cast(dict[str, str], dict(config_list[4]))
        extractor_cls = config_list[5]
        post_process = config_list[6] if len(config_list) > 6 else None  # type: ignore

        extractor = _get_extractor(path, listagem, table, key_cols, extra, post_process, extractor_cls)

        entities = _get_entities(conn)
        for empresa_id, empresa_name in entities.items():
            for year in years:
                raw_path = RAW_DIR / str(table) / f"{empresa_id}_{year}.json"
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

                    normalised = _normalize(rows, year, str(empresa_id), post_process)
                    count = upsert(conn, str(table), normalised, key_cols)  # type: ignore
                    logger.info("[%d/%d] %s / %s / %d → %d rows", done + 1, total, listagem, empresa_name, year, count)
                except Exception as exc:
                    logger.warning("SKIP %s / %s / %d: %s", listagem, empresa_name, year, exc)
                    _log_failed_request(listagem, empresa_name, year, exc)
                done += 1

    set_metadata(conn, "last_extracted_at", date.today().isoformat())
    logger.info("Pipeline complete.")


if __name__ == "__main__":
    run()
