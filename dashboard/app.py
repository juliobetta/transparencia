import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from shared import get_conn

import db

st.set_page_config(page_title="Transparência Porciúncula", layout="wide")
st.html(
    """
    <style>
    [data-testid='stStatusWidget'] { display: none; }

    /* Desabilita interações nos gráficos em telas menores e dispositivos touch para evitar que o zoom intercepte o scroll da página */
    @media (max-width: 1024px), (pointer: coarse) {
        [data-testid="stPlotlyChart"],
        .js-plotly-plot,
        .plotly .draglayer,
        .plotly .draglayer .drag,
        [class*="stPlotlyChart"] {
            pointer-events: none !important;
        }
    }
    </style>
    """
)

START_YEAR = 2021
_YEARS = list(reversed(range(START_YEAR, date.today().year + 1)))

if "sidebar_year" not in st.session_state:
    st.session_state["sidebar_year"] = _YEARS[0]

st.session_state["sidebar_year"] = st.sidebar.selectbox(
    "Ano",
    _YEARS,
    key="sidebar_year_selector",
    index=_YEARS.index(st.session_state["sidebar_year"]),
)

_engine = get_conn()
_empresas = db.get_empresas(_engine)
_emp_ids = list(_empresas.keys())
_emp_labels = list(_empresas.values())
_EMPRESA_PADRAO = "7"
if "sidebar_empresa" not in st.session_state:
    st.session_state["sidebar_empresa"] = _EMPRESA_PADRAO
_emp_current = st.session_state["sidebar_empresa"]
_emp_idx = _emp_ids.index(_emp_current) if _emp_current in _emp_ids else 0
_selected_label = st.sidebar.selectbox("Entidade", _emp_labels, index=_emp_idx, key="sidebar_empresa_selector")
st.session_state["sidebar_empresa"] = _emp_ids[_emp_labels.index(_selected_label)]
st.session_state["sidebar_empresa_nome"] = _selected_label
st.session_state["_empresas"] = _empresas

pages = {
    "": [
        st.Page("pages/visao_geral.py", title="Visão Geral", icon=":material/home:"),
    ],
    "Administrativo": [
        st.Page("pages/receitas.py", title="Receitas", icon=":material/payments:"),
        st.Page("pages/orcamento.py", title="Execução Orçamentária", icon=":material/account_balance_wallet:"),
        st.Page("pages/despesas.py", title="Despesas Detalhadas", icon=":material/receipt_long:"),
        st.Page("pages/licitacoes.py", title="Licitações e Contratos", icon=":material/gavel:"),
        st.Page("pages/pessoal.py", title="Pessoal", icon=":material/group:"),
    ],
    "Temas": [
        st.Page("pages/saude.py", title="Saúde", icon=":material/health_and_safety:"),
        st.Page("pages/caprem.py", title="CAPREM", icon=":material/account_balance:"),
    ],
    "Outros": [
        st.Page("pages/comparacao.py", title="Comparação", icon=":material/compare_arrows:"),
        st.Page("pages/dados_brutos.py", title="Dados Brutos", icon=":material/table:"),
    ],
}

pg = st.navigation(pages)
pg.run()
