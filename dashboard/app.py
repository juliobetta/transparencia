import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

st.set_page_config(page_title="Transparência Porciúncula", layout="wide")
st.html("<style>[data-testid='stStatusWidget'] { display: none; }</style>")

_YEARS = list(range(2022, date.today().year + 1))

if "sidebar_year" not in st.session_state:
    st.session_state["sidebar_year"] = _YEARS[-1]

st.session_state["sidebar_year"] = st.sidebar.selectbox(
    "Ano",
    _YEARS,
    key="sidebar_year_selector",
    index=_YEARS.index(st.session_state["sidebar_year"]),
)

pages = {
    "": [
        st.Page("pages/visao_geral.py", title="Visão Geral", icon=":material/home:"),
        st.Page("pages/receitas.py", title="Receitas", icon=":material/payments:"),
        st.Page("pages/orcamento.py", title="Execução Orçamentária", icon=":material/account_balance_wallet:"),
        st.Page("pages/despesas.py", title="Despesas Detalhadas", icon=":material/receipt_long:"),
        st.Page("pages/fornecedores.py", title="Fornecedores", icon=":material/store:"),
        st.Page("pages/licitacoes.py", title="Licitações e Contratos", icon=":material/gavel:"),
        st.Page("pages/pessoal.py", title="Pessoal", icon=":material/group:"),
        st.Page("pages/comparacao.py", title="Comparação", icon=":material/compare_arrows:"),
        st.Page("pages/dados_brutos.py", title="Dados Brutos", icon=":material/table:"),
    ],
    "Setores": [
        st.Page("pages/saude.py", title="Saúde", icon=":material/health_and_safety:"),
        st.Page("pages/caprem.py", title="CAPREM", icon=":material/account_balance:"),
    ],
}

pg = st.navigation(pages)
pg.run()
