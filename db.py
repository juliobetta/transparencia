import os
from typing import Union

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection, Engine
from sqlmodel import SQLModel, create_engine

import models  # registers all table models in SQLModel.metadata  # noqa: F401

_engine: Engine | None = None

Connectable = Union[Engine, Connection]


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        load_dotenv()
        url = os.environ["DATABASE_URL"]
        _engine = create_engine(url)
    return _engine


def create_tables(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)


def _execute(db: Connectable, stmt, params=None):
    if isinstance(db, Engine):
        with db.connect() as conn:
            result = conn.execute(stmt, params or {})
            conn.commit()
            return result
    else:
        return db.execute(stmt, params or {})


def upsert(db: Connectable, table_name: str, rows: list[dict], key_cols: list[str]) -> int:
    if not rows:
        return 0
    table = SQLModel.metadata.tables[table_name]
    valid_cols = {col.name for col in table.columns}
    filtered = [{k: v for k, v in r.items() if k in valid_cols} for r in rows]
    filtered = [r for r in filtered if r and all(r.get(k) is not None for k in key_cols)]
    if not filtered:
        return 0
    # Deduplicate by PK within the batch (last row wins, matching INSERT OR REPLACE behaviour).
    seen: dict[tuple, dict] = {}
    for r in filtered:
        seen[tuple(r.get(k) for k in key_cols)] = r
    filtered = list(seen.values())
    # Normalise all rows to the same key set so SQLAlchemy can build a uniform multi-row VALUES clause.
    all_cols = {k for r in filtered for k in r}
    filtered = [{k: r.get(k) for k in all_cols} for r in filtered]
    stmt = pg_insert(table).values(filtered)
    update_cols = {c: stmt.excluded[c] for c in all_cols if c not in key_cols}
    stmt = (
        stmt.on_conflict_do_update(index_elements=key_cols, set_=update_cols)
        if update_cols
        else stmt.on_conflict_do_nothing(index_elements=key_cols)
    )
    _execute(db, stmt)
    return len(filtered)


def set_metadata(db: Connectable, key: str, value: str) -> None:
    table = SQLModel.metadata.tables["metadata"]
    stmt = pg_insert(table).values(key=key, value=value)
    stmt = stmt.on_conflict_do_update(index_elements=["key"], set_={"value": value})
    _execute(db, stmt)


def get_metadata(db: Connectable, key: str) -> str | None:
    query = text("SELECT value FROM metadata WHERE key = :key")
    if isinstance(db, Engine):
        with db.connect() as conn:
            row = conn.execute(query, {"key": key}).fetchone()
    else:
        row = db.execute(query, {"key": key}).fetchone()
    return row[0] if row else None
