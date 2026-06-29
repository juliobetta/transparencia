import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

DASHBOARD_DIR = Path(__file__).parent.parent.parent / "dashboard"
PAGES_DIR = DASHBOARD_DIR / "pages"

# Make `shared` and `pages` importable without a Streamlit runtime
for _p in (str(DASHBOARD_DIR), str(PAGES_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_YEAR = 2024  # year used for all seeded test data


class _StreamlitMock:
    """Minimal Streamlit stand-in that returns sensible defaults so page top-level code runs."""

    session_state: dict = {"sidebar_year": _YEAR}
    column_config = MagicMock()
    sidebar = MagicMock()

    def cache_data(self, func=None, **_kwargs):
        if func is not None:
            return func
        return lambda fn: fn

    def cache_resource(self, func=None, **_kwargs):
        if func is not None:
            return func
        return lambda fn: fn

    def selectbox(self, _label, options, index=0, **_kwargs):
        return list(options)[index]

    def columns(self, spec):
        n = spec if isinstance(spec, int) else len(spec)
        return [MagicMock() for _ in range(n)]

    def tabs(self, labels):
        return [MagicMock() for _ in labels]

    def slider(self, _label, _min_value=None, _max_value=None, value=None, **_kwargs):
        return value

    def text_input(self, _label, value="", **_kwargs):
        return value

    def __getattr__(self, name):
        return MagicMock()


@pytest.fixture(scope="session")
def _seeded_engine(engine):
    """Seed one year of minimal data into all tables used by dashboard pages."""
    import db

    year = _YEAR
    emp = "7"

    with engine.connect() as conn:
        db.upsert(
            conn,
            "despesas_por_orgao",
            [
                {
                    "ano": year,
                    "empresa": emp,
                    "codigo": "01",
                    "descricao": "SAUDE",
                    "empenhado": "100000",
                    "liquidado": "90000",
                    "pago": "80000",
                    "dotac": "200000",
                    "altdo": "0",
                    "dotacao_atualizada": "200000",
                }
            ],
            ["ano", "empresa", "codigo"],
        )
        db.upsert(
            conn,
            "despesas_por_fornecedor",
            [
                {
                    "ano": year,
                    "empresa": emp,
                    "codigo": "F1",
                    "descricao": "FORNECEDOR A",
                    "empenhado": "100000",
                    "liquidado": "90000",
                    "pago": "80000",
                }
            ],
            ["ano", "empresa", "codigo"],
        )
        db.upsert(
            conn,
            "contratos",
            [
                {
                    "ano": year,
                    "empresa": emp,
                    "numero": "C1",
                    "fornecedor": "F1",
                    "objeto": "Objeto teste",
                    "valor": "10000",
                    "valcon": "10000",
                    "licitacao_numero": "",
                    "mes": "01",
                }
            ],
            ["ano", "empresa", "numero"],
        )
        db.upsert(
            conn,
            "pessoal",
            [
                {
                    "ano": year,
                    "empresa": emp,
                    "mes": "01",
                    "matricula": "M1",
                    "nome": "SERVIDOR A",
                    "cargo": "CARGO A",
                    "proventos": "5000",
                }
            ],
            ["ano", "empresa", "mes", "matricula"],
        )
        db.upsert(
            conn,
            "receita_orcamentaria",
            [
                {
                    "ano": year,
                    "empresa": emp,
                    "codigo": "1.1.1",
                    "descricao": "IPTU",
                    "previsto": "50000",
                    "previsao_atualizada": "50000",
                    "arrecadado_total": "45000",
                }
            ],
            ["ano", "empresa", "codigo"],
        )
        db.upsert(
            conn,
            "receita_uniao",
            [
                {
                    "ano": year,
                    "empresa": emp,
                    "codigo": "1721.00.00",
                    "descricao": "FPM",
                    "previsto": "200000",
                    "previsao_atualizada": "200000",
                    "arrecadado_total": "195000",
                }
            ],
            ["ano", "empresa", "codigo"],
        )
        db.upsert(
            conn,
            "receita_estado",
            [
                {
                    "ano": year,
                    "empresa": emp,
                    "codigo": "1722.00.00",
                    "descricao": "ICMS",
                    "previsto": "100000",
                    "previsao_atualizada": "100000",
                    "arrecadado_total": "98000",
                }
            ],
            ["ano", "empresa", "codigo"],
        )
        conn.commit()

    return engine


@pytest.fixture(scope="session")
def page_env(_seeded_engine):
    """Patch streamlit and shared helpers so pages can be imported against the test DB.

    Session-scoped: patching once avoids the sys.modules teardown/restore cycle that
    causes numpy C-extension double-load errors when patch.dict is used per test.
    """
    import shared

    mock_st = _StreamlitMock()

    # Manually set so teardown doesn't restore all of sys.modules
    _orig_streamlit = sys.modules.get("streamlit")
    _orig_st = getattr(shared, "st", None)
    _orig_get_conn = shared.get_conn

    sys.modules["streamlit"] = mock_st  # type: ignore[assignment]
    shared.st = mock_st  # type: ignore[assignment]
    shared.get_conn = lambda: _seeded_engine

    yield mock_st, _seeded_engine

    shared.get_conn = _orig_get_conn
    shared.st = _orig_st
    if _orig_streamlit is None:
        sys.modules.pop("streamlit", None)
    else:
        sys.modules["streamlit"] = _orig_streamlit
