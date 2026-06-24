import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import get_conn, render_sidebar

import glossary
from analysis import supplier_concentration

conn = get_conn()
year = render_sidebar()

st.header("Concentração de Fornecedores")
with st.expander("ℹ️ O que isso significa?"):
    st.write(f"**Fornecedor:** {glossary.tooltip('Fornecedor')}")
    st.write("**HHI:** Índice de concentração de mercado. Acima de 2.500 indica alta concentração.")
result = supplier_concentration.run(conn, year)
if result["dominante"]:
    st.warning(f"⚠️ {result['dominante']} recebeu mais de 40% do total pago a fornecedores.")
st.metric(
    "HHI (concentração)",
    f"{result['hhi']:,.0f}",
    help="Índice Herfindahl-Hirschman. Acima de 2.500 = concentração alta.",
)
st.dataframe(
    result["top10"][["descricao", "empenhado", "percentual"]].rename(
        columns={"descricao": "Fornecedor", "empenhado": "Empenhado (R$)", "percentual": "%"}
    ),
    use_container_width=True,
)
st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
