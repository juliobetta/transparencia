import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest
import testing.postgresql
import yaml
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlmodel import create_engine

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("PORTAL_SLUG", "porciuncula_prefeitura")

import elt.extract.porciuncula_prefeitura.models  # noqa: F401 — registers tables in SQLModel.metadata for db.upsert()

_PROFILES_DIR = str(Path(__file__).parent.parent / "elt" / "transform")
_SOURCES_YML = (
    Path(__file__).parent.parent
    / "elt"
    / "transform"
    / "models"
    / "staging"
    / "porciuncula_prefeitura"
    / "_sources.yml"
)

# PKs por tabela — necessários para o constraint PRIMARY KEY no banco de testes
_RAW_PKS: dict[str, list[str]] = {
    "empresas": ["id"],
    "despesas_gerais": ["ano", "empresa", "numero"],
    "despesas_por_orgao": ["ano", "empresa", "codigo"],
    "despesas_por_unidade": ["ano", "empresa", "codigo"],
    "despesas_por_fornecedor": ["ano", "empresa", "codigo"],
    "despesas_restos_pagar": ["ano", "empresa", "numero"],
    "despesas_extra_orcamentaria": ["ano", "empresa", "numero"],
    "receita_orcamentaria": ["ano", "empresa", "codigo"],
    "receita_uniao": ["ano", "empresa", "codigo"],
    "receita_estado": ["ano", "empresa", "codigo"],
    "receita_extra_orcamentaria": ["ano", "empresa", "codigo"],
    "licitacoes": ["ano", "empresa", "numero"],
    "contratos": ["ano", "empresa", "numero"],
    "diarias": ["ano", "empresa", "numero"],
    "emendas_impositivas": ["ano", "empresa", "numero"],
    "emendas_cad": ["ano", "empresa", "numero"],
    "pessoal": ["ano", "empresa", "mes", "matricula"],
    "transferencias": ["ano", "empresa", "codigo"],
    "metadata": ["portal_slug", "key"],
}


def _create_raw_schema(eng) -> None:
    """Cria schema raw e tabelas a partir de _sources.yml (fonte única de verdade)."""
    sources = yaml.safe_load(_SOURCES_YML.read_text())
    tables = sources["sources"][0]["tables"]

    with eng.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw_porciuncula_prefeitura"))
        for table_def in tables:
            name = table_def["name"]
            col_defs_list = table_def.get("columns", [])
            if not col_defs_list:
                continue
            pk_cols = _RAW_PKS.get(name, [])

            def _sql_type(col: dict) -> str:
                if "data_type" in col:
                    return col["data_type"]
                return "integer" if col["name"] == "ano" else "text"

            col_sql = ", ".join(f'"{c["name"]}" {_sql_type(c)}' for c in col_defs_list)
            pk_clause = f", PRIMARY KEY ({', '.join(pk_cols)})" if pk_cols else ""
            ddl = f'CREATE TABLE IF NOT EXISTS raw_porciuncula_prefeitura."{name}" ({col_sql}{pk_clause})'
            conn.execute(text(ddl))
        conn.commit()


def _run_dbt(pg_url: str, *args: str) -> None:
    u = urlparse(pg_url)
    env = {
        **os.environ,
        "DBT_HOST": u.hostname or "",
        "DBT_PORT": str(u.port or 5432),
        "DBT_USER": u.username or "",
        "DBT_PASSWORD": u.password or "",
        "DBT_DBNAME": u.path.lstrip("/"),
    }
    subprocess.run(
        ["dbt", *args, "--profiles-dir", _PROFILES_DIR, "--project-dir", _PROFILES_DIR],
        env=env,
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="session")
def pg():
    with testing.postgresql.Postgresql() as pg:
        yield pg


@pytest.fixture(scope="session")
def engine(pg):
    pg_url = pg.url()
    eng = create_engine(pg_url)
    # Raw schema e tabelas derivadas de _sources.yml
    _create_raw_schema(eng)
    # dbt cria staging/intermediate (views) e marts (views em test_mode) em public
    _run_dbt(pg_url, "deps")
    _run_dbt(pg_url, "seed")
    _run_dbt(pg_url, "run", "--vars", '{"test_mode": true}')
    return eng


@pytest.fixture
def conn(engine) -> Connection:
    with engine.connect() as connection:
        connection.execute(text("SET search_path = raw_porciuncula_prefeitura, public"))
        yield connection
        connection.rollback()
