import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import fmt_currency, get_conn, get_extraction_date, render_sidebar
from sqlalchemy.engine import Engine

import glossary
from analysis import caprem_story
from report.caprem import generate

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _caprem(conn, year, _extracted_at):
    return caprem_story.run(conn, year)


conn = get_conn()
year = render_sidebar()
_extracted_at = get_extraction_date(conn)

st.title("CAPREM (Caixa de Previdência Municipal)")
st.caption(f"Dados do CAPREM extraídos do [Portal de Transparência]({glossary.PORTAL_URL}).")

data = _caprem(conn, year, _extracted_at)

# Section 1: Repasses
st.header("① Repasses")
c1, c2 = st.columns(2)
c1.metric("Total de Repasses (R$)", fmt_currency(data.get("total_transfers", 0)))
c2.metric("Número de Operações", data.get("count_operations", 0))

# Section 2: Detalhes de Despesas
st.header("② Detalhes de Despesas")
if "despesas" in data and not data["despesas"].empty:
    st.dataframe(
        data["despesas"].rename(
            columns={
                "ano": "Ano",
                "descricao": "Descrição",
                "empenhado": "Empenhado",
                "liquidado": "Liquidado",
                "pago": "Pago",
                "empresa": "Empresa",
            }
        ),
        width="stretch",
        hide_index=True,
        column_config={
            "codigo": None,
            "insmf": None,
            "cepci": None,
            "Empresa": None,
            "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Liquidado": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
        },
    )
else:
    st.info("Sem detalhes de despesas registrados para este ano.")

# Export functionality
st.header("Exportar")

if "report_path" not in st.session_state:
    st.session_state["report_path"] = None

if st.button("Gerar Relatório HTML"):
    st.session_state["report_path"] = generate(conn, year)

if st.session_state["report_path"] is not None:
    path = st.session_state["report_path"]
    with open(path, "rb") as f:
        st.download_button("Baixar relatório (HTML)", f, file_name=f"caprem-{year}.html", mime="text/html")
