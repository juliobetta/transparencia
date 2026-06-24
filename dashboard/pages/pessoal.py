import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
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
    fig, ax = plt.subplots()
    ax.bar(df["ano"].astype(str), df["percentual_folha"], color="#2e86c1")
    ax.set_ylabel("% dos gastos")
    ax.set_title("Folha / Total de Gastos (%)")
    st.pyplot(fig)
st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
