import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from shared import (
    ANO_ATUAL,
    SPARK_CFG,
    fmt_compact,
    fmt_currency,
    get_conn,
    get_data_extracao,
    pct_delta,
    render_aviso_ano_parcial,
    render_sidebar,
    sparkline,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import execucao_orcamentaria, orcamento_funcional

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _orcamento(conn, year, _extracted_at):
    return execucao_orcamentaria.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _orcamento_by_year(conn, years, _extracted_at):
    return execucao_orcamentaria.summarize_by_year(conn, list(years))


conn = get_conn()
year = render_sidebar()
_extracted_at = get_data_extracao(conn)

st.title("Execução Orçamentária por Órgão")
st.caption("Entenda como a Prefeitura executa o orçamento ao longo do ano.")

if year == ANO_ATUAL:
    render_aviso_ano_parcial(year, _extracted_at)

df_orcamento = _orcamento(conn, year, _extracted_at)
totais = execucao_orcamentaria.summarize(df_orcamento)

_all_years = list(range(2022, year + 1))
_hist = _orcamento_by_year(conn, tuple(_all_years), _extracted_at)
_anos = _all_years
_dotacao_serie = [_hist[y]["total_dotacao"] for y in _anos]
_empenhado_serie = [_hist[y]["total_empenhado"] for y in _anos]
_liquidado_serie = [_hist[y]["total_liquidado"] for y in _anos]
_pago_serie = [_hist[y]["total_pago"] for y in _anos]

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(
        "Total Dotação",
        fmt_compact(totais["total_dotacao"]),
        delta=pct_delta(_dotacao_serie),
        delta_color="off",
        help=glossary.tooltip("Dotação Atualizada"),
    )
    st.plotly_chart(
        sparkline(_anos, _dotacao_serie, "#607D8B"), use_container_width=True, config=SPARK_CFG, key="spark_orc_dotacao"
    )
with c2:
    st.metric(
        "Total Empenhado",
        fmt_compact(totais["total_empenhado"]),
        delta=pct_delta(_empenhado_serie) if year != ANO_ATUAL else "—",
        delta_color="off",
        help=glossary.tooltip("Empenho"),
    )
    st.plotly_chart(
        sparkline(_anos, _empenhado_serie, "#2196F3"),
        use_container_width=True,
        config=SPARK_CFG,
        key="spark_orc_empenhado",
    )
with c3:
    st.metric(
        "Total Liquidado",
        fmt_compact(totais["total_liquidado"]),
        delta=pct_delta(_liquidado_serie) if year != ANO_ATUAL else "—",
        delta_color="off",
        help=glossary.tooltip("Liquidação"),
    )
    st.plotly_chart(
        sparkline(_anos, _liquidado_serie, "#4CAF50"),
        use_container_width=True,
        config=SPARK_CFG,
        key="spark_orc_liquidado",
    )
with c4:
    st.metric(
        "Total Pago",
        fmt_compact(totais["total_pago"]),
        delta=pct_delta(_pago_serie) if year != ANO_ATUAL else "—",
        delta_color="off",
        help=glossary.tooltip("Pagamento"),
    )
    st.plotly_chart(
        sparkline(_anos, _pago_serie, "#FF9800"), use_container_width=True, config=SPARK_CFG, key="spark_orc_pago"
    )

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
