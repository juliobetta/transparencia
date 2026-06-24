import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from shared import get_conn, render_sidebar

import glossary
from analysis import payroll_vs_services

conn = get_conn()
year = render_sidebar()

st.header("Folha de Pagamento")
with st.expander("ℹ️ O que isso significa?"):
    st.write("Percentual dos gastos pagos que corresponde à folha de pessoal (servidores municipais).")
df = payroll_vs_services.run(conn, list(range(2022, year + 1)))
if not df.empty:
    fig = px.bar(
        df,
        x="ano",
        y="percentual_folha",
        title="Folha / Total de Gastos (%)",
        labels={"ano": "Ano", "percentual_folha": "%"},
    )
    st.plotly_chart(fig, use_container_width=True)

# Granular Salary Analysis
st.subheader("Distribuição de Remuneração")
df_pessoal = pd.read_sql_query("SELECT remuneracao FROM pessoal WHERE ano = ?", conn, params=(year,))
df_pessoal["remuneracao"] = pd.to_numeric(df_pessoal["remuneracao"].str.replace(",", "."), errors="coerce").fillna(0)

if not df_pessoal.empty:
    fig_hist = px.histogram(
        df_pessoal,
        x="remuneracao",
        nbins=20,
        title="Distribuição das Remunerações",
        labels={"remuneracao": "Remuneração (R$)"},
    )
    st.plotly_chart(fig_hist, use_container_width=True)
st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
