import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
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
        values = [row["receita_propria"], row["transferencias_uniao"], row["transferencias_estado"]]
        if any(v > 0 for v in values):
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.pie(
                values,
                labels=["Receita Própria", "Transferências União", "Transferências Estado"],
                autopct="%1.1f%%",
                startangle=90,
            )
            ax.set_title("Distribuição de Receitas (Previsão Atualizada)")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.pyplot(fig, use_container_width=True)

            st.caption("Fonte: previsão atualizada — dados de arrecadação efetiva não disponíveis na API.")
        else:
            st.info("Sem dados de receita para o ano selecionado.")
        if row["alerta_dependencia"]:
            st.warning("⚠️ Receita própria abaixo de 10% — alta dependência de repasses federais/estaduais.")
st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
