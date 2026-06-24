import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import get_conn, render_sidebar

import glossary
from analysis import budget_execution

conn = get_conn()
year = render_sidebar()

st.header("Execução Orçamentária por Órgão")
with st.expander("ℹ️ O que isso significa?"):
    st.write(f"**Dotação Atualizada:** {glossary.tooltip('Dotação Atualizada')}")
    st.write(f"**Empenho:** {glossary.tooltip('Empenho')}")
df = budget_execution.run(conn, year)
st.dataframe(
    df[["descricao", "empenhado", "dotacao_atualizada", "taxa_execucao", "alerta"]].rename(
        columns={
            "descricao": "Órgão",
            "empenhado": "Empenhado (R$)",
            "dotacao_atualizada": "Dotação (R$)",
            "taxa_execucao": "Taxa de Execução",
            "alerta": "Situação",
        }
    ),
    use_container_width=True,
)
st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
