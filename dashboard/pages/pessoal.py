import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from shared import get_conn, get_extraction_date, render_sidebar
from sqlalchemy import text
from sqlalchemy.engine import Engine

import glossary
from analysis import payroll_vs_services

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _payroll(conn, year, _extracted_at):
    return payroll_vs_services.run(conn, list(range(2022, year + 1)))


conn = get_conn()
year = render_sidebar()
_extracted_at = get_extraction_date(conn)

st.header("Folha de Pagamento")
with st.expander("ℹ️ O que isso significa?"):
    st.write("Percentual dos gastos pagos que corresponde à folha de pessoal (servidores municipais).")
df = _payroll(conn, year, _extracted_at)
if not df.empty:
    fig = px.bar(
        df,
        x="ano",
        y="percentual_folha",
        title="Folha / Total de Gastos (%)",
        labels={"ano": "Ano", "percentual_folha": "%"},
    )
    fig.update_xaxes(tickmode="linear", dtick=1)
    fig.update_traces(hovertemplate="Ano: %{x}<br>Percentual: %{y:.2f}%")
    st.plotly_chart(fig, width="stretch")

# Granular Salary Analysis
st.subheader("Distribuição de Remuneração")
df_pessoal = pd.read_sql_query(text("SELECT remuneracao FROM pessoal WHERE ano = :ano"), conn, params={"ano": year})
df_pessoal["remuneracao"] = pd.to_numeric(df_pessoal["remuneracao"].str.replace(",", "."), errors="coerce").fillna(0)

if not df_pessoal.empty:
    fig_hist = px.histogram(
        df_pessoal,
        x="remuneracao",
        nbins=20,
        title="Distribuição das Remunerações",
        labels={"remuneracao": "Remuneração"},
    )
    fig_hist.update_traces(hovertemplate="Remuneração: R$ %{x:,.2f}<br>Contagem: %{y}")
    st.plotly_chart(fig_hist, width="stretch")
st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
