import db


def test_create_tables_creates_expected_tables(engine):  # noqa: ARG001
    from sqlmodel import SQLModel

    table_names = set(SQLModel.metadata.tables.keys())
    assert "despesas_por_orgao" in table_names
    assert "licitacoes" in table_names
    assert "pessoal" in table_names


def test_upsert_inserts_rows(conn):
    rows = [
        {
            "ano": 2025,
            "empresa": "7",
            "codigo": "01",
            "descricao": "SAUDE",
            "empenhado": "1000",
            "liquidado": "900",
            "pago": "800",
            "dotac": "2000",
            "altdo": "0",
            "dotacao_atualizada": "2000",
        },
    ]
    count = db.upsert(conn, "despesas_por_orgao", rows, key_cols=["ano", "empresa", "codigo"])
    assert count == 1
    from sqlalchemy import text

    row = conn.execute(
        text("SELECT descricao FROM despesas_por_orgao WHERE ano=2025 AND empresa='7' AND codigo='01'")
    ).fetchone()
    assert row is not None
    assert row[0] == "SAUDE"


def test_upsert_replaces_on_conflict(conn):
    row = {
        "ano": 2025,
        "empresa": "7",
        "codigo": "02",
        "descricao": "SAUDE",
        "empenhado": "1000",
        "liquidado": "900",
        "pago": "800",
        "dotac": "2000",
        "altdo": "0",
        "dotacao_atualizada": "2000",
    }
    db.upsert(conn, "despesas_por_orgao", [row], key_cols=["ano", "empresa", "codigo"])
    row["empenhado"] = "1500"
    db.upsert(conn, "despesas_por_orgao", [row], key_cols=["ano", "empresa", "codigo"])
    from sqlalchemy import text

    result = conn.execute(
        text("SELECT empenhado FROM despesas_por_orgao WHERE ano=2025 AND empresa='7' AND codigo='02'")
    ).fetchone()
    assert result[0] == "1500"
    count = conn.execute(
        text("SELECT COUNT(*) FROM despesas_por_orgao WHERE ano=2025 AND empresa='7' AND codigo='02'")
    ).fetchone()[0]
    assert count == 1


def test_set_and_get_metadata(conn):
    db.set_metadata(conn, "test_key", "test_value")
    result = db.get_metadata(conn, "test_key")
    assert result == "test_value"


def test_get_metadata_returns_none_for_missing_key(conn):
    result = db.get_metadata(conn, "nonexistent_key_xyz")
    assert result is None
