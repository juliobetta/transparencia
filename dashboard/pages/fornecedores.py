import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
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
        columns={"descricao": "Fornecedor", "empenhado": "Empenhado", "percentual": "%"}
    ),
    column_config={
        "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
        "%": st.column_config.NumberColumn(format="%.2f%%"),
    },
    use_container_width=True,
    hide_index=True,
)

# Pie chart
# We need to fetch the total from despesas_por_fornecedor to calculate "Others"
df_all = pd.read_sql_query("SELECT empenhado FROM despesas_por_fornecedor WHERE ano = ?", conn, params=(year,))
df_all["empenhado"] = pd.to_numeric(df_all["empenhado"].str.replace(",", "."), errors="coerce").fillna(0)
total_all = df_all["empenhado"].sum()

top10 = result["top10"].copy()
top10_sum = top10["empenhado"].sum()
others_sum = total_all - top10_sum

pie_data = pd.concat(
    [
        top10[["descricao", "empenhado"]].rename(columns={"descricao": "Fornecedor"}),
        pd.DataFrame({"Fornecedor": ["Outros"], "empenhado": [others_sum]}),
    ]
)

fig = px.pie(pie_data, values="empenhado", names="Fornecedor", title="Distribuição do Empenhado")
st.plotly_chart(fig, use_container_width=True)

st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")

st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
