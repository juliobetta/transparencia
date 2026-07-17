import sys
from pathlib import Path
from typing import Any

import constants

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from shared import (
    ANO_ATUAL,
    ANO_INICIAL,
    SPARK_CFG,
    fmt_compact,
    fmt_currency,
    get_conn,
    get_data_extracao,
    pct_delta,
    render_aviso_ano_parcial,
    render_breadcrumb,
    render_sidebar,
    sparkline,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import execucao_orcamentaria, orcamento_funcional, tendencias_anuais

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _orcamento(conn, year, empresa_ids, _extracted_at):
    return execucao_orcamentaria.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _orcamento_by_year(conn, years, empresa_ids, _extracted_at):
    return execucao_orcamentaria.summarize_by_year(conn, list(years), empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _yoy(conn, years, empresa_ids, _extracted_at):
    return tendencias_anuais.run(conn, years, empresa_ids=empresa_ids)


conn = get_conn()
year, empresa_ids = render_sidebar()
_extracted_at = get_data_extracao(conn)

st.title("Execução Orçamentária por Órgão")
render_breadcrumb(year, empresa_ids)
st.caption("Entenda como a Prefeitura executa o orçamento ao longo do ano.")

if year == ANO_ATUAL:
    render_aviso_ano_parcial(year, _extracted_at)

df_orcamento = _orcamento(conn, year, empresa_ids, _extracted_at)
totais = execucao_orcamentaria.summarize(df_orcamento)

_all_years = list(range(ANO_INICIAL, year + 1))
_hist = _orcamento_by_year(conn, tuple(_all_years), empresa_ids, _extracted_at)
_anos = _all_years
_dotacao_serie = [_hist[y]["total_dotacao"] for y in _anos]
_empenhado_serie = [_hist[y]["total_empenhado"] for y in _anos]
_liquidado_serie = [_hist[y]["total_liquidado"] for y in _anos]
_pago_serie = [_hist[y]["total_pago"] for y in _anos]

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(
        "Dotação Atualizada",
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
df_funcional = orcamento_funcional.get_orcamento_funcional(conn, year, empresa_ids=empresa_ids)
df_funcional_resumo = (
    df_funcional.groupby("funcao_nome")[["dotacao_atualizada", "empenhado", "liquidado", "pago"]]
    .sum()
    .reset_index()
    .sort_values("pago", ascending=True)
)
df_funcional_resumo["ValorFormatado"] = df_funcional_resumo["pago"].apply(fmt_currency)

fig_barras = px.bar(
    df_funcional_resumo,
    x="pago",
    y="funcao_nome",
    orientation="h",
    title="Execução Orçamentária por Função (Valor Pago)",
    labels={"pago": "Pago (R$)", "funcao_nome": "Função"},
    text="ValorFormatado",
)
fig_barras.update_traces(textposition="auto")
fig_barras.update_layout(margin=dict(r=50))
st.plotly_chart(fig_barras, use_container_width=True)

with st.expander("Ver Detalhamento por Função"):
    st.dataframe(
        df_funcional_resumo[["funcao_nome", "dotacao_atualizada", "liquidado", "empenhado", "pago"]]
        .rename(
            columns={
                "funcao_nome": "Função",
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

st.markdown("---")
st.subheader("Tendências Históricas")

yoy = _yoy(conn, _all_years, empresa_ids, _extracted_at)
anos_yoy = yoy["ano"].tolist()

col_tendencia, col_pressao = st.columns([6, 4])

with col_tendencia:
    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Bar(
            x=anos_yoy,
            y=yoy["total_empenhado"].tolist(),
            name="Empenhado",
            marker_color="rgba(33,150,243,0.35)",
        )
    )
    fig_trend.add_trace(
        go.Bar(
            x=anos_yoy,
            y=yoy["total_gasto"].tolist(),
            name="Pago",
            marker_color="#2196F3",
        )
    )
    fig_trend.update_layout(
        title="Empenhado vs Pago por Ano",
        barmode="overlay",
        xaxis=dict(dtick=1, tickformat="d"),
        yaxis=dict(tickformat=",.0f", tickprefix="R$ "),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        margin=dict(l=0, r=0, t=40, b=60),
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    st.caption(
        "A barra clara mostra o total comprometido (empenhado); a barra sólida mostra o que efetivamente saiu para fornecedores (pago). "
        "Quanto menor a diferença entre as duas, maior a eficiência de pagamento no exercício."
    )

with col_pressao:
    _pressao = tendencias_anuais.gap_pressao_fiscal(yoy)
    anos_pressao = _pressao["anos"]
    lacuna = _pressao["gap"]
    cores = _pressao["colors"]
    opacidade = [0.4 if a == ANO_ATUAL else 1.0 for a in anos_pressao]
    fig_pct = go.Figure(
        go.Bar(
            x=anos_pressao,
            y=lacuna,
            marker_color=cores,
            marker_opacity=opacidade,
            hovertemplate="%{x}<br>Pressão: %{y:+.2f}%<extra></extra>",
        )
    )
    fig_pct.add_hline(y=0, line_width=1, line_color="rgba(0,0,0,0.3)")
    if ANO_ATUAL in anos_pressao:
        lacuna_parcial = lacuna[anos_pressao.index(ANO_ATUAL)]
        fig_pct.add_annotation(
            x=ANO_ATUAL,
            y=lacuna_parcial,
            text="ano parcial",
            showarrow=False,
            yshift=10 if lacuna_parcial >= 0 else -16,
            font=dict(size=10, color="rgba(0,0,0,0.45)"),
        )
    fig_pct.update_layout(
        title="Pressão Fiscal Anual",
        xaxis=dict(dtick=1, tickformat="d"),
        yaxis=dict(ticksuffix="%"),
        hovermode="x unified",
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=60),
    )
    st.plotly_chart(fig_pct, use_container_width=True)
    st.caption(
        "Barras acima do zero indicam que o total pago cresceu mais do que a receita naquele ano — sinal de pressão fiscal."
    )

st.caption(f"[Ver no portal oficial →]({constants.PORTAL_URL})")
