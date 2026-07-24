import sys
from pathlib import Path
from typing import Any

import constants

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.graph_objects as go
import streamlit as st
from shared import (
    ANO_ATUAL,
    ANO_INICIAL,
    COLOR_ACCENT,
    bar_chart_h,
    fmt_compact,
    funnel_waterfall,
    get_conn,
    get_data_extracao,
    kpi_card,
    kpi_grid,
    page_header,
    partial_year_month,
    pct_delta,
    plotly_card_end,
    plotly_card_layout,
    plotly_card_start,
    render_aviso_ano_parcial,
    render_sidebar,
    section_heading,
)
from sqlalchemy.engine import Engine

from app.analytics import execucao_orcamentaria, orcamento_funcional, tendencias_anuais

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

_partial_suffix = f"parcial, Jan–{partial_year_month(_extracted_at)}" if year == ANO_ATUAL else ""
_eyebrow = f"Administrativo · Exercício {year}" + (f" ({_partial_suffix})" if _partial_suffix else "")
st.html(
    page_header(
        _eyebrow,
        "Execução Orçamentária",
        "Cada real passa por quatro estágios legais antes de sair do caixa: "
        "<strong style='color:#1a1d21'>reservar</strong> (empenho), "
        "<strong style='color:#1a1d21'>confirmar a entrega</strong> (liquidação) e "
        "<strong style='color:#1a1d21'>pagar</strong>. Veja quanto do orçamento já avançou em cada etapa.",
    )
)

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

_dot = totais["total_dotacao"]
_emp = totais["total_empenhado"]
_liq = totais["total_liquidado"]
_pago = totais["total_pago"]
_pct_emp = _emp / _dot if _dot > 0 else 0.0
_pct_liq = _liq / _dot if _dot > 0 else 0.0
_pct_pago = _pago / _dot if _dot > 0 else 0.0

st.html(
    kpi_grid(
        kpi_card("Dotação Atualizada", fmt_compact(_dot), sub=pct_delta(_dotacao_serie) or ""),
        kpi_card("Total Empenhado", fmt_compact(_emp), sub=f"{_pct_emp:.1%} da dotação", accent=True),
        kpi_card("Total Liquidado", fmt_compact(_liq), sub=f"{_pct_liq:.1%} da dotação", accent=True),
        kpi_card("Total Pago", fmt_compact(_pago), sub=f"{_pct_pago:.1%} da dotação", accent=True),
        cols=4,
    )
)

st.html(section_heading("Funil da execução"))
st.html(
    funnel_waterfall(
        [
            ("Dotação", _dot, fmt_compact(_dot)),
            ("Empenhado", _emp, fmt_compact(_emp)),
            ("Liquidado", _liq, fmt_compact(_liq)),
            ("Pago", _pago, fmt_compact(_pago)),
        ],
        _dot,
    )
)

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

df_funcional = orcamento_funcional.get_orcamento_funcional(conn, year, empresa_ids=empresa_ids)
df_funcional_resumo = (
    df_funcional.groupby("funcao_nome")[["dotacao_atualizada", "empenhado", "liquidado", "pago"]]
    .sum()
    .reset_index()
    .sort_values("pago", ascending=False)
)

st.html(section_heading("Para onde vai o gasto, por função", aside="valor pago · R$ mi"))
if not df_funcional_resumo.empty:
    _func_rows = [
        (str(r["funcao_nome"]), float(r["pago"]), fmt_compact(float(r["pago"])))
        for _, r in df_funcional_resumo.head(8).iterrows()
    ]
    st.html(bar_chart_h(_func_rows))

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

with st.expander("📈 Ver Tendências Históricas"):
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
                marker_color="rgba(58,127,193,0.33)",
            )
        )
        fig_trend.add_trace(
            go.Bar(
                x=anos_yoy,
                y=yoy["total_gasto"].tolist(),
                name="Pago",
                marker_color=COLOR_ACCENT,
            )
        )
        fig_trend.update_layout(
            **plotly_card_layout("Empenhado vs Pago por Ano", height=320),
            barmode="overlay",
            xaxis=dict(dtick=1, tickformat="d"),
            yaxis=dict(tickformat=",.0f", tickprefix="R$ "),
            hovermode="x unified",
        )
        st.html(plotly_card_start())
        st.plotly_chart(fig_trend, use_container_width=True)
        st.html(plotly_card_end())
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
            **plotly_card_layout("Pressão Fiscal Anual", height=320),
            xaxis=dict(dtick=1, tickformat="d"),
            yaxis=dict(ticksuffix="%"),
            hovermode="x unified",
        )
        st.html(plotly_card_start())
        st.plotly_chart(fig_pct, use_container_width=True)
        st.html(plotly_card_end())
        st.caption(
            "Barras acima do zero indicam que o total pago cresceu mais do que a receita naquele ano — sinal de pressão fiscal."
        )

st.caption(f"[Ver no portal oficial →]({constants.PORTAL_URL})")
