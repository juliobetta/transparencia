"""CLI: load raw JSON files from a run directory into the raw_<slug> PostgreSQL schema."""

import argparse
import importlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import cast

from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from config import PortalConfig
from db import get_engine, set_metadata
from elt.extract.base import EndpointConfig

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


def _sanitize_key(k: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", k.lower()).strip("_")


def _extract_month(row: dict) -> str | None:
    for field in ["dtassi", "datae", "dtpublic", "dataadmissao"]:
        if field in row and row[field]:
            try:
                return datetime.strptime(row[field], "%d/%m/%Y %H:%M:%S").strftime("%m")
            except ValueError:
                continue
    if "referencia_nome" in row and row["referencia_nome"]:
        parts = row["referencia_nome"].split(" - ")
        if len(parts) > 1:
            return _MONTH_MAP.get(parts[1].strip())
    return None


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
        mes = _extract_month(normalised)
        if mes:
            normalised["mes"] = mes
        out.append(normalised)
    return out


def _ensure_table(engine, schema: str, table: str, cols: list[str], key_cols: list[str]) -> None:
    """Create schema and table with TEXT columns; add missing columns to existing tables."""
    valid_keys = [k for k in key_cols if k in cols]
    if not valid_keys:
        valid_keys = [cols[0]] if cols else []

    pk_def = ", ".join(f'"{k}"' for k in valid_keys)
    col_defs = ",\n    ".join(f'"{c}" TEXT' for c in cols)

    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        if pk_def:
            conn.execute(
                text(
                    f'CREATE TABLE IF NOT EXISTS "{schema}"."{table}" (\n    {col_defs},\n    PRIMARY KEY ({pk_def})\n)'
                )
            )
        else:
            conn.execute(text(f'CREATE TABLE IF NOT EXISTS "{schema}"."{table}" (\n    {col_defs}\n)'))
        for col in cols:
            conn.execute(text(f'ALTER TABLE "{schema}"."{table}" ADD COLUMN IF NOT EXISTS "{col}" TEXT'))


def _upsert_raw(engine, schema: str, table: str, rows: list[dict], key_cols: list[str]) -> int:
    if not rows:
        return 0

    all_cols = sorted({k for row in rows for k in row.keys()})
    valid_keys = [k for k in key_cols if k in all_cols]
    non_pk_cols = [c for c in all_cols if c not in valid_keys]

    _ensure_table(engine, schema, table, all_cols, key_cols)

    meta = MetaData()
    tbl = Table(table, meta, schema=schema, autoload_with=engine)

    # Normalise all rows to same key set; cast values to str for the raw TEXT schema
    normalised = [{c: str(row[c]) if row.get(c) is not None else None for c in all_cols} for row in rows]
    # Deduplicate by PK within batch (last row wins)
    seen: dict[tuple, dict] = {}
    for row in normalised:
        seen[tuple(row.get(k) for k in valid_keys)] = row
    deduped = list(seen.values())

    stmt = pg_insert(tbl).values(deduped)
    if valid_keys and non_pk_cols:
        stmt = stmt.on_conflict_do_update(
            index_elements=valid_keys,
            set_={c: stmt.excluded[c] for c in non_pk_cols},
        )
    elif valid_keys:
        stmt = stmt.on_conflict_do_nothing(index_elements=valid_keys)

    with engine.begin() as conn:
        conn.execute(stmt)

    return len(deduped)


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Load raw JSON files into raw_<slug> PostgreSQL schema")
    parser.add_argument("--portal", required=True, help="Portal slug (e.g. porciuncula_prefeitura)")
    parser.add_argument("--dir", help="Raw run directory path (default: latest under data/raw_runs/)")
    args = parser.parse_args()

    portal = PortalConfig.load(args.portal)
    mod = importlib.import_module(f"elt.extract.{portal.slug}.api_endpoints")
    endpoint_configs = cast(list[EndpointConfig], mod.ENDPOINT_CONFIGS)
    schema = portal.raw_schema

    run_dir_path = args.dir
    if not run_dir_path:
        run_dirs = [d for d in Path("data/raw_runs").iterdir() if d.is_dir()]
        if not run_dirs:
            raise ValueError("No raw run directories found under data/raw_runs")
        run_dir_path = str(max(run_dirs, key=lambda d: d.stat().st_mtime))

    run_dir = Path(run_dir_path)
    if not run_dir.exists():
        raise ValueError(f"Directory {run_dir_path} does not exist.")

    try:
        extraction_dt = datetime.strptime(run_dir.name, "%Y%m%d_%H%M%S")
        extraction_date = extraction_dt.isoformat(sep=" ")
    except ValueError:
        extraction_date = None

    engine = get_engine()

    for json_file in sorted(run_dir.rglob("*.json")):
        table = json_file.parent.name
        config = next((c for c in endpoint_configs if c.table == table), None)
        if not config:
            logger.warning("No endpoint config for table: %s", table)
            continue

        key_cols = list(config.key_cols)
        parts = json_file.stem.split("_")
        empresa_id = parts[0]
        year = int(parts[1])

        # Both exigibilidade split-tables load into the same target table
        target_table = "despesas_por_exigibilidade" if "despesas_por_exigibilidade" in table else table

        rows = json.loads(json_file.read_text(encoding="utf-8"))
        normalised = _normalize(rows, year, empresa_id, config.post_process)
        count = _upsert_raw(engine, schema, target_table, normalised, key_cols)
        logger.info("Loaded %s / %s / %d → %d rows into %s.%s", table, empresa_id, year, count, schema, target_table)

    if extraction_date:
        with engine.begin() as conn:
            set_metadata(conn, "last_extracted_at", extraction_date)
        logger.info("Set extraction date: %s", extraction_date)

    logger.info("Load complete → schema: %s", schema)


if __name__ == "__main__":
    main()
