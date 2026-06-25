import json
import logging
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path

from db import create_tables, get_connection, set_metadata, upsert
from extractors.extractors import ENDPOINT_CONFIGS


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


def run(years: list[int] | None = None, start_from: str | None = None, only: str | None = None) -> None:
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

    for config in ENDPOINT_CONFIGS:
        path, listagem, table, key_cols, extra, extractor_cls, *post_process = config
        post_process = post_process[0] if post_process else None

        extractor = _get_extractor(path, listagem, table, key_cols, extra, post_process, extractor_cls)

        entities = _get_entities(conn)
        for empresa_id, empresa_name in entities.items():
            for year in years:
                try:
                    rows = extractor.extract(empresa_id, year)
                    raw_path = RAW_DIR / table / f"{empresa_id}_{year}.json"
                    raw_path.parent.mkdir(parents=True, exist_ok=True)
                    raw_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
                    normalised = _normalize(rows, year, str(empresa_id), post_process)
                    count = upsert(conn, table, normalised, key_cols)
                    logger.info("[%d/%d] %s / %s / %d → %d rows", done + 1, total, listagem, empresa_name, year, count)
                except Exception as exc:
                    logger.warning("SKIP %s / %s / %d: %s", listagem, empresa_name, year, exc)
                done += 1

    set_metadata(conn, "last_extracted_at", date.today().isoformat())
    logger.info("Pipeline complete.")


if __name__ == "__main__":
    run()
