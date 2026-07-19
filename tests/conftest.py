import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest
import testing.postgresql
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlmodel import SQLModel, create_engine

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("PORTAL_SLUG", "porciuncula_prefeitura")

import models  # noqa: F401 — registers all tables in SQLModel.metadata

_PROFILES_DIR = str(Path(__file__).parent.parent / "elt" / "transform")


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
    # Criar schema raw e todas as tabelas brutas nele (sem alterar models.py)
    raw_eng = eng.execution_options(schema_translate_map={None: "raw_porciuncula_prefeitura"})
    with raw_eng.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw_porciuncula_prefeitura"))
        conn.commit()
    SQLModel.metadata.create_all(raw_eng)
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
