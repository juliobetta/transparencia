import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from shared import get_conn, render_sidebar

import glossary
from analysis import revenue_sources

conn = get_conn()
year = render_sidebar()

st.header("Fontes de Receita")
st.info(
    "⚠️ O portal de transparência só disponibiliza dados de receita para o exercício corrente. "
    "Comparações históricas não estão disponíveis via API."
)
with st.expander("ℹ️ O que isso significa?"):
    st.write(f"**Receita Própria:** {glossary.tooltip('Receita Própria')}")
    st.write(f"**FPM:** {glossary.tooltip('FPM (Fundo de Participação dos Municípios)')}")
df = revenue_sources.run(conn, list(range(2022, year + 1)))
if not df.empty:
    row = df[df["ano"] == year]
    if not row.empty:
        row = row.iloc[0]

        # Summary Table
        st.subheader("Resumo: Previsto vs. Arrecadado")
        resumo_df = pd.DataFrame(
            {
                "Fonte": ["Receita Própria", "Transferências União", "Transferências Estado"],
                "Previsto (R$)": [row["receita_propria"], row["transferencias_uniao"], row["transferencias_estado"]],
                # Assuming 'arrecadado' is not available based on previous code comment
            }
        )
        st.dataframe(resumo_df, use_container_width=True, hide_index=True)

        # Plotly Pie Chart
        fig = px.pie(
            resumo_df,
            values="Previsto (R$)",
            names="Fonte",
            title="Distribuição de Receitas (Previsão Atualizada)",
        )
        st.plotly_chart(fig, use_container_width=True)

        if row["alerta_dependencia"]:
            st.warning("⚠️ Receita própria abaixo de 10% — alta dependência de repasses federais/estaduais.")
st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
