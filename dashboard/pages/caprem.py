import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import fmt_currency, get_conn, render_sidebar

import glossary
from analysis import caprem_story
from report.caprem import generate

conn = get_conn()
year = render_sidebar()

st.title("CAPREM (Caixa de Previdência Municipal)")
st.caption(f"Dados do CAPREM extraídos do [Portal de Transparência]({glossary.PORTAL_URL}).")

data = caprem_story.run(conn, year)

# Section 1: Repasses
st.header("① Repasses")
c1, c2 = st.columns(2)
c1.metric("Total de Repasses (R$)", fmt_currency(data.get("total_transfers", 0)))
c2.metric("Número de Operações", data.get("count_operations", 0))

# Section 2: Detalhes de Despesas
st.header("② Detalhes de Despesas")
if "despesas" in data and not data["despesas"].empty:
    st.dataframe(data["despesas"], use_container_width=True, hide_index=True)
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
