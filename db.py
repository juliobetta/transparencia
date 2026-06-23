import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "transparencia.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS despesas_por_orgao (
    ano INTEGER, empresa TEXT, codigo TEXT, descricao TEXT,
    empenhado TEXT, liquidado TEXT, pago TEXT,
    dotac TEXT, altdo TEXT, dotacao_atualizada TEXT,
    PRIMARY KEY (ano, empresa, codigo)
);
CREATE TABLE IF NOT EXISTS despesas_por_unidade (
    ano INTEGER, empresa TEXT, codigo TEXT, descricao TEXT,
    empenhado TEXT, liquidado TEXT, pago TEXT,
    dotac TEXT, altdo TEXT, dotacao_atualizada TEXT,
    PRIMARY KEY (ano, empresa, codigo)
);
CREATE TABLE IF NOT EXISTS despesas_por_fornecedor (
    ano INTEGER, empresa TEXT, codigo TEXT, descricao TEXT,
    empenhado TEXT, liquidado TEXT, pago TEXT,
    PRIMARY KEY (ano, empresa, codigo)
);
CREATE TABLE IF NOT EXISTS despesas_gerais (
    ano INTEGER, empresa TEXT, numero TEXT, descricao TEXT,
    fornecedor TEXT, empenhado TEXT, liquidado TEXT, pago TEXT,
    data_empenho TEXT, orgao TEXT,
    PRIMARY KEY (ano, empresa, numero)
);
CREATE TABLE IF NOT EXISTS despesas_restos_pagar (
    ano INTEGER, empresa TEXT, numero TEXT, descricao TEXT,
    fornecedor TEXT, valor TEXT, situacao TEXT,
    PRIMARY KEY (ano, empresa, numero)
);
CREATE TABLE IF NOT EXISTS despesas_extra_orcamentaria (
    ano INTEGER, empresa TEXT, numero TEXT, descricao TEXT,
    fornecedor TEXT, valor TEXT,
    PRIMARY KEY (ano, empresa, numero)
);
CREATE TABLE IF NOT EXISTS despesas_por_exigibilidade (
    ano INTEGER, empresa TEXT, tipo TEXT, valor TEXT,
    PRIMARY KEY (ano, empresa, tipo)
);
CREATE TABLE IF NOT EXISTS diarias (
    ano INTEGER, empresa TEXT, numero TEXT, beneficiario TEXT,
    valor TEXT, destino TEXT, data TEXT,
    PRIMARY KEY (ano, empresa, numero)
);
CREATE TABLE IF NOT EXISTS receita_orcamentaria (
    ano INTEGER, empresa TEXT, codigo TEXT, descricao TEXT,
    previsto TEXT, arrecadado TEXT,
    PRIMARY KEY (ano, empresa, codigo)
);
CREATE TABLE IF NOT EXISTS receita_uniao (
    ano INTEGER, empresa TEXT, codigo TEXT, descricao TEXT,
    previsto TEXT, arrecadado TEXT,
    PRIMARY KEY (ano, empresa, codigo)
);
CREATE TABLE IF NOT EXISTS receita_estado (
    ano INTEGER, empresa TEXT, codigo TEXT, descricao TEXT,
    previsto TEXT, arrecadado TEXT,
    PRIMARY KEY (ano, empresa, codigo)
);
CREATE TABLE IF NOT EXISTS receita_extra_orcamentaria (
    ano INTEGER, empresa TEXT, codigo TEXT, descricao TEXT,
    valor TEXT,
    PRIMARY KEY (ano, empresa, codigo)
);
CREATE TABLE IF NOT EXISTS receita_detalhes (
    ano INTEGER, empresa TEXT, codigo TEXT, descricao TEXT,
    previsto TEXT, arrecadado TEXT,
    PRIMARY KEY (ano, empresa, codigo)
);
CREATE TABLE IF NOT EXISTS licitacoes (
    ano INTEGER, empresa TEXT, numero TEXT, modalidade TEXT,
    objeto TEXT, valor TEXT, situacao TEXT, data_abertura TEXT,
    PRIMARY KEY (ano, empresa, numero)
);
CREATE TABLE IF NOT EXISTS contratos (
    ano INTEGER, empresa TEXT, numero TEXT, fornecedor TEXT,
    objeto TEXT, valor TEXT, data_inicio TEXT, data_fim TEXT,
    licitacao_numero TEXT,
    PRIMARY KEY (ano, empresa, numero)
);
CREATE TABLE IF NOT EXISTS transferencias (
    ano INTEGER, empresa TEXT, codigo TEXT, descricao TEXT,
    valor TEXT,
    PRIMARY KEY (ano, empresa, codigo)
);
CREATE TABLE IF NOT EXISTS emendas_impositivas (
    ano INTEGER, empresa TEXT, numero TEXT, descricao TEXT,
    valor TEXT,
    PRIMARY KEY (ano, empresa, numero)
);
CREATE TABLE IF NOT EXISTS emendas_cad (
    ano INTEGER, empresa TEXT, numero TEXT, descricao TEXT,
    valor TEXT,
    PRIMARY KEY (ano, empresa, numero)
);
CREATE TABLE IF NOT EXISTS pessoal (
    ano INTEGER, empresa TEXT, mes TEXT, matricula TEXT,
    nome TEXT, cargo TEXT, remuneracao TEXT,
    PRIMARY KEY (ano, empresa, mes, matricula)
);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def _ensure_columns(conn: sqlite3.Connection, table: str, cols: list[str]) -> None:
    if not re.match(r"^[a-z_][a-z0-9_]*$", table):
        raise ValueError(f"Invalid table name: {table!r}")
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    for col in cols:
        if not re.match(r"^[a-z_][a-z0-9_]*$", col):
            raise ValueError(f"Invalid column name from API: {col!r}")
        if col not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
    conn.commit()


def set_metadata(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", (key, value))
    conn.commit()


def get_metadata(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def upsert(conn: sqlite3.Connection, table: str, rows: list[dict], key_cols: list[str]) -> int:  # noqa: ARG001
    if not rows:
        return 0
    cols = list(rows[0].keys())
    _ensure_columns(conn, table, cols)
    placeholders = ", ".join("?" for _ in cols)
    col_names = ", ".join(cols)
    sql = f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})"
    values = [tuple(r.get(c) for c in cols) for r in rows]
    conn.executemany(sql, values)
    conn.commit()
    return len(rows)
