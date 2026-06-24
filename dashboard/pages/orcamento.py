import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import fmt_currency, get_conn, render_sidebar

import glossary
from analysis import budget_execution

conn = get_conn()
year = render_sidebar()

st.header("Execução Orçamentária por Órgão")
with st.expander("ℹ️ O que isso significa?"):
    st.write(f"**Dotação Atualizada:** {glossary.tooltip('Dotação Atualizada')}")
    st.write(f"**Empenho:** {glossary.tooltip('Empenho')}")
df = budget_execution.run(conn, year)

# Summary Metrics
total_empenhado = df["empenhado"].sum()
total_dotacao = df["dotacao_atualizada"].sum()

c1, c2 = st.columns(2)
c1.metric("Total Empenhado", fmt_currency(total_empenhado))
c2.metric("Total Dotação", fmt_currency(total_dotacao))

# Chart
fig = px.bar(
    df.sort_values("empenhado", ascending=False),
    x="descricao",
    y="empenhado",
    title="Empenhado por Órgão",
    labels={"descricao": "Órgão", "empenhado": "Empenhado"},
)
# Update chart trace to format tooltip
fig.update_traces(hovertemplate="Órgão: %{x}<br>Empenhado: R$ %{y:,.2f}")
fig.update_layout(yaxis_tickformat=",.2f")

st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    df[["descricao", "empenhado", "dotacao_atualizada", "taxa_execucao", "alerta"]].rename(
        columns={
            "descricao": "Órgão",
            "empenhado": "Empenhado",
            "dotacao_atualizada": "Dotação",
            "taxa_execucao": "Taxa de Execução",
            "alerta": "Situação",
        }
    ),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
        "Dotação": st.column_config.NumberColumn(format="R$ %,.2f"),
        "Taxa de Execução": st.column_config.NumberColumn(format="%.2f%%"),
    },
)
st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
