import os
from typing import Union

from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Connection, Engine
from sqlmodel import create_engine

from config import PortalConfig

_engine: Engine | None = None
_table_cache: dict[tuple[str, str], Table] = {}

Connectable = Union[Engine, Connection]


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        load_dotenv()
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        _engine = create_engine(url)
    return _engine


def create_tables(engine: Engine) -> None:
    pass  # tabelas raw criadas dinamicamente pelo elt/load; noop mantido para compatibilidade


def _get_table(db: Connectable, table_name: str) -> Table:
    engine = db.engine if isinstance(db, Connection) else db
    schema = PortalConfig.load().raw_schema
    key = (str(engine.url), f"{schema}.{table_name}")
    if key not in _table_cache:
        meta = MetaData()
        with engine.connect() as conn:
            meta.reflect(bind=conn, schema=schema, only=[table_name])
        _table_cache[key] = meta.tables[f"{schema}.{table_name}"]
    return _table_cache[key]


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
    table = _get_table(db, table_name)
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


def set_metadata(db: Connectable, key: str, value: str, portal_slug: str) -> None:
    table = _get_table(db, "metadata")
    stmt = pg_insert(table).values(portal_slug=portal_slug, key=key, value=value)
    stmt = stmt.on_conflict_do_update(index_elements=["portal_slug", "key"], set_={"value": value})
    _execute(db, stmt)


def get_metadata(db: Connectable, key: str, portal_slug: str) -> str | None:
    query = text("SELECT value FROM dim_metadata WHERE key = :key AND portal_slug = :slug")
    if isinstance(db, Engine):
        with db.connect() as conn:
            row = conn.execute(query, {"key": key, "slug": portal_slug}).fetchone()
    else:
        row = db.execute(query, {"key": key, "slug": portal_slug}).fetchone()
    return row[0] if row else None


def get_empresas(conn: Connectable) -> dict[str, str]:
    """Retorna {id_str: nome} das entidades cadastradas no banco."""
    query = text("SELECT empresa_id, orgao_nome FROM dim_orgao ORDER BY empresa_id")
    if isinstance(conn, Engine):
        with conn.connect() as c:
            rows = c.execute(query).fetchall()
    else:
        rows = conn.execute(query).fetchall()
    return {str(row[0]): row[1] for row in rows}
