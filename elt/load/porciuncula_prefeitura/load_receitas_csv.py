"""Load receitas CSV files from data/csv/receitas/ into the raw_porciuncula_prefeitura PostgreSQL schema."""

import re
import unicodedata
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from config import PortalConfig
from db import get_engine
from elt.extract.base import EndpointConfig
from elt.extract.porciuncula_prefeitura.api_endpoints import ENDPOINT_CONFIGS

TABLE_MAPPING = {
    "ReceitaOrcamentaria": "receita_orcamentaria",
    "ReceitaUniao": "receita_uniao",
    "ReceitaEstado": "receita_estado",
    "ReceitaExtraOrcamentaria": "receita_extra_orcamentaria",
    "DetalhesReceitaOrcamentaria": "receita_detalhes",
    "ReceitaDetalhes": "receita_detalhes",
    "ReceitaDetalhe": "receita_detalhes",
}


def _sanitize_key(k: str) -> str:
    nfkd = unicodedata.normalize("NFKD", k)
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", ascii_str.lower()).strip("_")


def _ensure_table(engine, schema: str, table: str, cols: list[str], key_cols: list[str]) -> None:
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
    normalised = [{c: str(row[c]) if row.get(c) is not None else None for c in all_cols} for row in rows]
    seen: dict[tuple, dict] = {}
    for row in normalised:
        seen[tuple(row.get(k) for k in valid_keys)] = row
    deduped = list(seen.values())
    stmt = pg_insert(tbl).values(deduped)
    if valid_keys and non_pk_cols:
        stmt = stmt.on_conflict_do_update(index_elements=valid_keys, set_={c: stmt.excluded[c] for c in non_pk_cols})
    elif valid_keys:
        stmt = stmt.on_conflict_do_nothing(index_elements=valid_keys)
    with engine.begin() as conn:
        conn.execute(stmt)
    return len(deduped)


def main() -> None:
    load_dotenv()

    portal = PortalConfig.load("porciuncula_prefeitura")
    schema = portal.raw_schema
    engine = get_engine()

    config_by_table: dict[str, EndpointConfig] = {c.table: c for c in ENDPOINT_CONFIGS}

    csv_dir = Path("data/csv/receitas")

    if not csv_dir.exists():
        raise FileNotFoundError(f"Directory '{csv_dir}' not found")

    csv_files = sorted(csv_dir.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in '{csv_dir}'")
        return

    for file_path in csv_files:
        parts = file_path.stem.split("_")
        if len(parts) < 3:
            print(f"Skipping {file_path.name}: expected <empresa>_<ano>_<endpoint>.csv")
            continue

        empresa_id = parts[0]
        try:
            year = int(parts[1])
        except ValueError:
            print(f"Skipping {file_path.name}: invalid year '{parts[1]}'")
            continue

        endpoint_raw = "_".join(parts[2:])
        table_name = TABLE_MAPPING.get(endpoint_raw) or next(
            (v for k, v in TABLE_MAPPING.items() if k.lower() == endpoint_raw.lower()), None
        )
        if not table_name:
            print(f"Skipping {file_path.name}: unknown endpoint '{endpoint_raw}'")
            continue

        if file_path.stat().st_size == 0:
            print(f"Skipping {file_path.name}: empty file")
            continue

        try:
            df = pd.read_csv(file_path, sep=None, engine="python", encoding="utf-8")
        except Exception as exc:
            print(f"Error reading {file_path.name}: {exc}")
            continue

        if df.empty:
            print(f"Skipping {file_path.name}: no rows")
            continue

        df.columns = [_sanitize_key(c) for c in df.columns]
        df["ano"] = year
        df["empresa"] = empresa_id

        if "codigo" not in df.columns:
            print(f"Skipping {file_path.name}: no 'codigo' column (incompatible with API table structure)")
            continue

        config = config_by_table.get(table_name)
        pk_cols = list(config.key_cols) if config else ["ano", "empresa", "codigo"]
        post_process = config.post_process if config else None

        df = df.dropna(subset=["ano", "empresa", "codigo"])
        df = df[df["codigo"].astype(str).str.strip().ne("")]

        if df.empty:
            print(f"Skipping {file_path.name}: no valid rows after filtering nulls")
            continue

        rows = [{k: (None if pd.isna(v) else v) for k, v in row.items()} for row in df.to_dict("records")]

        if post_process:
            rows = [post_process(row) for row in rows]

        count = _upsert_raw(engine, schema, table_name, rows, pk_cols)
        print(f"✓ {file_path.name} → {count} rows into {schema}.{table_name}")


if __name__ == "__main__":
    main()
