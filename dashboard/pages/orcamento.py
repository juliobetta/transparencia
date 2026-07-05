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
def _orcamento(conn, year, _extracted_at):
    return execucao_orcamentaria.run(conn, year)


conn = get_conn()
year = render_sidebar()
_extracted_at = get_extraction_date(conn)

st.title("Execução Orçamentária por Órgão")
st.caption("Entenda como a Prefeitura executa o orçamento ao longo do ano.")

df_orcamento = _orcamento(conn, year, _extracted_at)
totais = execucao_orcamentaria.summarize(df_orcamento)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Dotação", fmt_compact(totais["total_dotacao"]), help=glossary.tooltip("Dotação Atualizada"))
c2.metric("Total Empenhado", fmt_compact(totais["total_empenhado"]), help=glossary.tooltip("Empenho"))
c3.metric("Total Liquidado", fmt_compact(totais["total_liquidado"]), help=glossary.tooltip("Liquidação"))
c4.metric("Total Pago", fmt_compact(totais["total_pago"]), help=glossary.tooltip("Pagamento"))

# Gráfico de Funil (Órgão)
dados_resumo = pd.DataFrame(
    {
        "Estágio": ["Dotação", "Empenhado", "Liquidado", "Pago"],
        "Valor": [
            totais["total_dotacao"],
            totais["total_empenhado"],
            totais["total_liquidado"],
            totais["total_pago"],
        ],
        "ValorFormatado": [
            fmt_currency(totais["total_dotacao"]),
            fmt_currency(totais["total_empenhado"]),
            fmt_currency(totais["total_liquidado"]),
            fmt_currency(totais["total_pago"]),
        ],
    }
)
fig_funil = px.funnel(
    dados_resumo,
    x="Valor",
    y="Estágio",
    text="ValorFormatado",
    title="Funil da Execução Orçamentária",
)
fig_funil.update_traces(
    textposition="inside",
    texttemplate="%{text}",
    hovertemplate="Estágio: %{y}<br>Valor: %{text}<extra></extra>",
)
st.plotly_chart(fig_funil, use_container_width=True)

with st.expander("Ver Detalhamento por Órgão"):
    st.dataframe(
        df_orcamento[["descricao", "empenhado", "dotacao_atualizada", "taxa_execucao", "alerta"]].rename(
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

# Gráfico de Barras (Função)
st.markdown("---")
df_funcional = orcamento_funcional.get_orcamento_funcional(conn, year)
df_funcional_resumo = (
    df_funcional.groupby("funcaonome")[["dotacao_atualizada", "empenhado", "liquidado", "pago"]]
    .sum()
    .reset_index()
    .sort_values("pago", ascending=True)
)
df_funcional_resumo["ValorFormatado"] = df_funcional_resumo["pago"].apply(fmt_currency)

fig_barras = px.bar(
    df_funcional_resumo,
    x="pago",
    y="funcaonome",
    orientation="h",
    title="Execução Orçamentária por Função (Valor Pago)",
    labels={"pago": "Pago (R$)", "funcaonome": "Função"},
    text="ValorFormatado",
)
fig_barras.update_traces(textposition="auto")
fig_barras.update_layout(margin=dict(r=50))
st.plotly_chart(fig_barras, use_container_width=True)

with st.expander("Ver Detalhamento por Função"):
    st.dataframe(
        df_funcional_resumo[["funcaonome", "dotacao_atualizada", "liquidado", "empenhado", "pago"]]
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
