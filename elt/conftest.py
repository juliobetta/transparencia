import os
import subprocess
import sys
from pathlib import Path
from typing import Iterator

import pytest
import yaml
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlmodel import create_engine

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("PORTAL_SLUG", "porciuncula_prefeitura")


_PROFILES_DIR = str(Path(__file__).parent / "transform")
_SOURCES_YML = Path(__file__).parent / "transform" / "models" / "staging" / "porciuncula_prefeitura" / "_sources.yml"


def _create_raw_schema(eng) -> None:
    """Cria schema raw e tabelas a partir de _sources.yml (fonte única de verdade)."""
    sources = yaml.safe_load(_SOURCES_YML.read_text())
    tables = sources["sources"][0]["tables"]

    def _sql_type(col: dict) -> str:
        if "data_type" in col:
            return col["data_type"]
        return "integer" if col["name"] == "ano" else "text"

    with eng.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw_porciuncula_prefeitura"))
        for table_def in tables:
            name = table_def["name"]
            col_defs_list = table_def.get("columns", [])
            if not col_defs_list:
                continue
            pk_cols = table_def.get("meta", {}).get("primary_key", [])
            col_sql = ", ".join(f'"{c["name"]}" {_sql_type(c)}' for c in col_defs_list)
            pk_clause = f", PRIMARY KEY ({', '.join(pk_cols)})" if pk_cols else ""
            ddl = f'CREATE TABLE IF NOT EXISTS raw_porciuncula_prefeitura."{name}" ({col_sql}{pk_clause})'
            conn.execute(text(ddl))
        conn.commit()


def _run_dbt(db_path: str, *args: str) -> None:
    env = {
        **os.environ,
        "DBT_DUCKDB_PATH": db_path,
        "DBT_ALLOW_EXPERIMENTAL_ADAPTERS": "true",
    }
    env.pop("DBT_DATABASE", None)
    try:
        subprocess.run(
            ["dbt", *args, "--profiles-dir", _PROFILES_DIR, "--project-dir", _PROFILES_DIR],
            env=env,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            print(f"dbt stderr: {exc.stderr.decode()}", file=sys.stderr)
        raise


@pytest.fixture(scope="session")
def engine(tmp_path_factory):
    db_dir = tmp_path_factory.mktemp("duckdb")
    db_path = str(db_dir / "test.duckdb")

    eng = create_engine(f"duckdb:///{db_path}")
    _create_raw_schema(eng)
    eng.dispose()

    _run_dbt(db_path, "deps")
    _run_dbt(db_path, "seed")
    _run_dbt(db_path, "run", "--vars", '{"test_mode": true}')

    eng = create_engine(f"duckdb:///{db_path}")
    yield eng
    eng.dispose()


@pytest.fixture
def conn(engine) -> Iterator[Connection]:
    with engine.connect() as connection:
        trans = connection.begin()
        connection.execute(text("SET search_path = 'raw_porciuncula_prefeitura,main'"))
        try:
            yield connection
        finally:
            trans.rollback()
