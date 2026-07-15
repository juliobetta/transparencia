import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import streamlit.components.v1 as components
from shared import get_conn

import db

st.set_page_config(page_title="Transparência Porciúncula", layout="wide")
st.html(
    """
    <style>
    [data-testid='stStatusWidget'] { display: none; }

    /* Remove truncamento nos itens do multiselect */
    .stMain {
        [data-baseweb="menu"] [role="option"],
        [data-baseweb="menu"] li {
            height: auto !important;
            white-space: normal !important;
            word-break: break-word !important;
        }
        [data-baseweb="menu"] [role="option"] span,
        [data-baseweb="menu"] li span {
            overflow: visible !important;
            text-overflow: unset !important;
            white-space: normal !important;
        }
        [data-baseweb="tag"],
        [data-baseweb="tag"] span {
            max-width: none !important;
            overflow: visible !important;
            text-overflow: unset !important;
            white-space: normal !important;
        }
    }

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

components.html(
    """
    <script>
    (function () {
        const T = {
            "Select all": "Selecionar tudo",
            "Deselect all": "Desmarcar tudo",
            "Choose options": "Escolha as opções",
            "No results": "Sem resultados"
        };
        const doc = window.parent.document;
        function translate() {
            const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT, null);
            let n;
            while ((n = walker.nextNode())) {
                if (T[n.textContent]) n.textContent = T[n.textContent];
            }
        }
        new MutationObserver(translate).observe(doc.body, { childList: true, subtree: true });
        translate();
    })();
    </script>
    """,
    height=0,
)

START_YEAR = 2021
_YEARS = list(reversed(range(START_YEAR, date.today().year + 1)))

if "sidebar_year" not in st.session_state:
    st.session_state["sidebar_year"] = _YEARS[0]

st.session_state["sidebar_year"] = st.sidebar.selectbox(
    "Ano",
    _YEARS,
    index=_YEARS.index(st.session_state["sidebar_year"]),
)

_engine = get_conn()
_empresas = db.get_empresas(_engine)
_emp_ids = list(_empresas.keys())
_emp_labels = list(_empresas.values())
_selected_labels: list[str] = st.sidebar.multiselect(
    "Entidade",
    _emp_labels,
    default=st.session_state.get("sidebar_empresa_nomes", _emp_labels),
)
_selected_ids = [_emp_ids[_emp_labels.index(label)] for label in _selected_labels]
st.session_state["sidebar_empresa_ids"] = None if set(_selected_ids) == set(_emp_ids) else _selected_ids or None
st.session_state["sidebar_empresa_nomes"] = _selected_labels
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
}

pg = st.navigation(pages)
pg.run()
