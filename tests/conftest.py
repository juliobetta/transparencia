import sys
from pathlib import Path

import pytest
import testing.postgresql
from sqlalchemy.engine import Connection
from sqlmodel import SQLModel, create_engine

sys.path.insert(0, str(Path(__file__).parent.parent))

import models  # noqa: F401 — registers all tables in SQLModel.metadata


@pytest.fixture(scope="session")
def pg():
    with testing.postgresql.Postgresql() as pg:
        yield pg


@pytest.fixture(scope="session")
def engine(pg):
    eng = create_engine(pg.url())
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def conn(engine) -> Connection:
    with engine.connect() as connection:
        yield connection
        connection.rollback()
