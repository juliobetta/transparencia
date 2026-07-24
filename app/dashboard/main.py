import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import streamlit.components.v1 as components
from shared import get_conn

import db
from config import PortalConfig

try:
    _slug = st.secrets.get("PORTAL_SLUG")
except Exception:
    _slug = None
_slug = _slug or os.environ.get("PORTAL_SLUG")
_config = PortalConfig.load(_slug)
st.session_state["portal_config"] = _config

st.set_page_config(page_title=f"Transparência {_config.display_name}", layout="wide")
st.html(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet">
    <style>
    :root {
        --ink: #1a1d21;
        --muted: #6b7280;
        --subtle: #9aa1ab;
        --line: #e7e9ee;
        --bg: #f4f5f7;
        --card: #fff;
        --accent: oklch(0.55 0.11 250);
        --alert: oklch(0.65 0.13 65);
        --risk: oklch(0.55 0.11 25);
        --positive: oklch(0.5 0.13 145);
    }

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        font-family: 'IBM Plex Sans', sans-serif !important;
        color: var(--ink);
        background-color: var(--bg);
    }

    .serif { font-family: 'Source Serif 4', serif !important; }

    /* ── Sidebar ────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid var(--line) !important;
    }
    [data-testid="stSidebarNav"] a {
        border-radius: 9px;
        padding: 9px 12px;
        transition: background 0.15s;
        color: #4b5563;
        font-weight: 500;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: oklch(0.55 0.11 250 / 0.08);
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: oklch(0.55 0.11 250 / 0.11);
        color: oklch(0.45 0.14 255) !important;
        font-weight: 600;
    }

    /* ── Ribbon ─────────────────────────────────────── */
    .ribbon {
        padding: 9px 0;
        background: #eef4fd;
        border-bottom: 1px solid #dfe9f8;
        font-size: 11.5px;
        color: #3a5a86;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 2rem;
    }
    .ribbon::before {
        content: '';
        display: inline-block;
        width: 6px; height: 6px;
        border-radius: 50%;
        background: oklch(0.55 0.11 250);
        flex-shrink: 0;
    }

    /* ── Keep existing rules ────────────────────────── */
    [data-testid='stStatusWidget'] { display: none; }

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

_YEARS = list(reversed(range(_config.ano_inicial, date.today().year + 1)))

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
