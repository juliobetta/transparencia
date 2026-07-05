import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from shared import (
    fmt_compact,
    fmt_currency,
    get_conn,
    get_extraction_date,
    render_sidebar,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import execucao_orcamentaria, orcamento_funcional

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _budget(conn, year, _extracted_at):
    return execucao_orcamentaria.run(conn, year)


conn = get_conn()
year = render_sidebar()
_extracted_at = get_extraction_date(conn)

st.title("Execução Orçamentária por Órgão")
st.caption("Entenda como a Prefeitura executa o orçamento ao longo do ano.")

df = _budget(conn, year, _extracted_at)
totals = execucao_orcamentaria.summarize(df)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Dotação", fmt_compact(totals["total_dotacao"]), help=glossary.tooltip("Dotação Atualizada"))
c2.metric("Total Empenhado", fmt_compact(totals["total_empenhado"]), help=glossary.tooltip("Empenho"))
c3.metric("Total Liquidado", fmt_compact(totals["total_liquidado"]), help=glossary.tooltip("Liquidação"))
c4.metric("Total Pago", fmt_compact(totals["total_pago"]), help=glossary.tooltip("Pagamento"))

# Funnel Chart (Órgão)
summary_data = pd.DataFrame(
    {
        "Estágio": ["Dotação", "Empenhado", "Liquidado", "Pago"],
        "Valor": [
            totals["total_dotacao"],
            totals["total_empenhado"],
            totals["total_liquidado"],
            totals["total_pago"],
        ],
        "ValorFormatado": [
            fmt_currency(totals["total_dotacao"]),
            fmt_currency(totals["total_empenhado"]),
            fmt_currency(totals["total_liquidado"]),
            fmt_currency(totals["total_pago"]),
        ],
    }
)
fig_funnel = px.funnel(
    summary_data,
    x="Valor",
    y="Estágio",
    text="ValorFormatado",
    title="Funil da Execução Orçamentária",
)
fig_funnel.update_traces(
    textposition="inside",
    texttemplate="%{text}",
    hovertemplate="Estágio: %{y}<br>Valor: %{text}<extra></extra>",
)
st.plotly_chart(fig_funnel, use_container_width=True)

with st.expander("Ver Detalhamento por Órgão"):
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

# Bar Chart (Função)
st.markdown("---")
df_func = orcamento_funcional.get_orcamento_funcional(conn, year)
df_func_summary = (
    df_func.groupby("funcaonome")[["dotacao_atualizada", "empenhado", "liquidado", "pago"]]
    .sum()
    .reset_index()
    .sort_values("pago", ascending=True)
)
df_func_summary["ValorFormatado"] = df_func_summary["pago"].apply(fmt_currency)

fig_bar = px.bar(
    df_func_summary,
    x="pago",
    y="funcaonome",
    orientation="h",
    title="Execução Orçamentária por Função (Valor Pago)",
    labels={"pago": "Pago (R$)", "funcaonome": "Função"},
    text="ValorFormatado",
)
fig_bar.update_traces(textposition="auto")
fig_bar.update_layout(margin=dict(r=50))
st.plotly_chart(fig_bar, use_container_width=True)

with st.expander("Ver Detalhamento por Função"):
    st.dataframe(
        df_func_summary[["funcaonome", "dotacao_atualizada", "liquidado", "empenhado", "pago"]]
        .rename(
            columns={
                "funcaonome": "Função",
                "dotacao_atualizada": "Total Dotação",
                "empenhado": "Total Empenhado",
                "liquidado": "Total Liquidado",
                "pago": "Total Pago",
            }
        )
        .sort_values(by="Total Pago", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "Total Dotação": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Total Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Total Liquidado": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Total Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
        },
        column_order=[
            "Função",
            "Total Dotação",
            "Total Empenhado",
            "Total Liquidado",
            "Total Pago",
        ],
    )

st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
