import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import fmt_currency, get_conn, get_extraction_date, render_sidebar
from sqlalchemy.engine import Engine

import glossary
from analysis import budget_execution

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _budget(conn, year, _extracted_at):
    return budget_execution.run(conn, year)


conn = get_conn()
year = render_sidebar()
_extracted_at = get_extraction_date(conn)

st.header("Execução Orçamentária por Órgão")
df = _budget(conn, year, _extracted_at)
totals = budget_execution.summarize(df)

c1, c2, c3 = st.columns(3)
c1.metric("Total Empenhado", fmt_currency(totals["total_empenhado"]), help=glossary.tooltip("Empenho"))
c2.metric("Total Dotação", fmt_currency(totals["total_dotacao"]), help=glossary.tooltip("Dotação Atualizada"))
c3.metric(
    "Saldo Orçamentário Disponível",
    fmt_currency(totals["saldo_orcamentario"]),
    help="Dotação Atualizada − Valor Empenhado. Indica o espaço legal restante para novos empenhos. Não representa disponibilidade em caixa.",
)

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

st.plotly_chart(fig, width="stretch")

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
    width="stretch",
    hide_index=True,
    column_config={
        "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
        "Dotação": st.column_config.NumberColumn(format="R$ %,.2f"),
        "Taxa de Execução": st.column_config.NumberColumn(format="%.2f%%"),
    },
)
st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
