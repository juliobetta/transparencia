import pytest

import db
from analysis.concentracao_fornecedores import hhi_por_ano, run


@pytest.fixture
def conn(conn):
    db.upsert(
        conn,
        "despesas_por_fornecedor",
        [
            {
                "ano": 2025,
                "empresa": "7",
                "codigo": "01",
                "descricao": "ALFA LTDA",
                "empenhado": "600000",
                "liquidado": "0",
                "pago": "0",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "codigo": "02",
                "descricao": "BETA ME",
                "empenhado": "200000",
                "liquidado": "0",
                "pago": "0",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "codigo": "03",
                "descricao": "GAMA SA",
                "empenhado": "200000",
                "liquidado": "0",
                "pago": "0",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    # Adicionar registros em despesas_gerais para que o JOIN funcione
    db.upsert(
        conn,
        "despesas_gerais",
        [
            {"ano": 2025, "empresa": "7", "numero": "1", "nomefor": "ALFA LTDA", "elemento": "30"},
            {"ano": 2025, "empresa": "7", "numero": "2", "nomefor": "BETA ME", "elemento": "36"},
            {"ano": 2025, "empresa": "7", "numero": "3", "nomefor": "GAMA SA", "elemento": "39"},
        ],
        ["ano", "empresa", "numero"],
    )
    return conn


def test_top10_has_correct_columns(conn):
    result = run(conn, 2025)
    assert {"codigo", "descricao", "empenhado", "percentual"}.issubset(result["top10"].columns)


def test_top10_sorted_descending(conn):
    result = run(conn, 2025)
    vals = result["top10"]["empenhado"].tolist()
    assert vals == sorted(vals, reverse=True)


def test_hhi_computed(conn):
    result = run(conn, 2025)
    assert result["hhi"] == pytest.approx(4400, rel=0.01)


def test_fornecedor_dominante_detectado(conn):
    result = run(conn, 2025)
    assert result["dominante"] == "ALFA LTDA"


def test_sem_dominante_quando_equilibrado(conn):
    rows = [
        {
            "ano": 2026,
            "empresa": "7",
            "codigo": str(i),
            "descricao": f"F{i}",
            "empenhado": "100000",
            "liquidado": "0",
            "pago": "0",
        }
        for i in range(5)
    ]
    db.upsert(conn, "despesas_por_fornecedor", rows, ["ano", "empresa", "codigo"])


def test_fornecedor_elemento_43_e_servico_incluido(conn):
    # Caso: Fornecedor tem elemento 43 (subvenção) E elemento 30 (material - whitelist)
    # Deve ser incluído.
    db.upsert(
        conn,
        "despesas_por_fornecedor",
        [
            {
                "ano": 2026,
                "empresa": "7",
                "codigo": "430",
                "descricao": "ASSOCIAÇÃO MISTA",
                "empenhado": "1000",
                "liquidado": "0",
                "pago": "1000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "despesas_gerais",
        [
            # Registro com elemento 43
            {"ano": 2026, "empresa": "7", "numero": "100", "nomefor": "ASSOCIAÇÃO MISTA", "elemento": "43"},
            # Registro com elemento da Whitelist
            {"ano": 2026, "empresa": "7", "numero": "101", "nomefor": "ASSOCIAÇÃO MISTA", "elemento": "30"},
        ],
        ["ano", "empresa", "numero"],
    )
    result = run(conn, 2026)

    # Verifica se a associação está presente nos resultados
    assert any(result["top10"]["descricao"] == "ASSOCIAÇÃO MISTA")
    assert result["total_all"] >= 1000.0


def test_fornecedor_apenas_43_excluido(conn):
    # Caso: Fornecedor tem APENAS elemento 43 (subvenção pura)
    # Deve ser excluído.
    db.upsert(
        conn,
        "despesas_por_fornecedor",
        [
            {
                "ano": 2026,
                "empresa": "7",
                "codigo": "431",
                "descricao": "ASSOCIAÇÃO PURA",
                "empenhado": "5000",
                "liquidado": "0",
                "pago": "5000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "despesas_gerais",
        [
            {"ano": 2026, "empresa": "7", "numero": "200", "nomefor": "ASSOCIAÇÃO PURA", "elemento": "43"},
        ],
        ["ano", "empresa", "numero"],
    )
    result = run(conn, 2026)

    # Verifica que a associação pura não está presente
    assert not any(result["top10"]["descricao"] == "ASSOCIAÇÃO PURA")
    # Total deve ser menor do que incluir os 5000 da associação pura
    assert result["total_all"] < 5000.0


def test_hhi_por_ano(conn):
    # conn fixture inserts 2025 data: ALFA 60%, BETA 20%, GAMA 20% → HHI ≈ 4400
    result = hhi_por_ano(conn, [2025])
    assert 2025 in result
    assert result[2025] == pytest.approx(4400, rel=0.01)
