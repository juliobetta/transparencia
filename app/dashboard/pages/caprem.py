import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import (
    ANO_ATUAL,
    bar_chart_h,
    fmt_compact,
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

import constants
from app.analytics import historia_caprem
from app.report.caprem import generate

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}

_MESES_PT = {
    "01": "Jan",
    "02": "Fev",
    "03": "Mar",
    "04": "Abr",
    "05": "Mai",
    "06": "Jun",
    "07": "Jul",
    "08": "Ago",
    "09": "Set",
    "10": "Out",
    "11": "Nov",
    "12": "Dez",
}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _caprem(conn, year, _extracted_at):
    return historia_caprem.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _pdf(conn, year, _extracted_at):
    return generate(conn, year)


conn = get_conn()
year, _ = render_sidebar()
_extracted_at = get_data_extracao(conn)

_partial_suffix = f"parcial, Jan–{partial_year_month(_extracted_at)}" if year == ANO_ATUAL else ""
_eyebrow = f"Previdência Municipal · Exercício {year}" + (f" ({_partial_suffix})" if _partial_suffix else "")

col_header, col_pdf = st.columns([7, 1])
with col_header:
    st.html(
        page_header(
            _eyebrow,
            "CAPREM",
            "Repasses da Prefeitura à Caixa de Previdência Municipal — "
            "valores empenhados, liquidados e pagos por entidade e função.",
        )
    )
with col_pdf:
    st.write("")
    st.write("")
    st.write("")
    pdf_bytes = _pdf(conn, year, _extracted_at)
    st.download_button(
        label="⬇ PDF",
        data=pdf_bytes,
        file_name=f"caprem-{year}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

if year == ANO_ATUAL:
    render_aviso_ano_parcial(year, _extracted_at)

data = _caprem(conn, year, _extracted_at)

trend = data.get("tendencia_anual")
_all_years = sorted(trend["ano"].tolist()) if trend is not None and not trend.empty else []


def _trend_val(col: str) -> list:
    if trend is None or trend.empty or col not in trend.columns:
        return []
    return list(trend.set_index("ano")[col].reindex(_all_years, fill_value=0))


_emp_serie = _trend_val("empenhado")
_pago_serie = _trend_val("pago")
_liq_serie = _trend_val("liquidado")

# ── KPIs ────────────────────────────────────────────────────────────────────
st.html(section_heading("Repasses", numbered="①"))
st.html(
    kpi_grid(
        kpi_card(
            "Total Empenhado",
            fmt_compact(data.get("total_transferencias", 0)),
            sub=pct_delta(_emp_serie) or "",
            accent=True,
        ),
        kpi_card(
            "Total Liquidado", fmt_compact(data.get("total_liquidado", 0)), sub=pct_delta(_liq_serie) or "", accent=True
        ),
        kpi_card("Total Pago", fmt_compact(data.get("total_pago", 0)), sub=pct_delta(_pago_serie) or "", accent=True),
        kpi_card("Taxa de Pagamento", f"{data.get('taxa_execucao', 0):.1%}"),
        cols=4,
    )
)

# ── Tendência histórica ──────────────────────────────────────────────────────
st.html(section_heading("Tendência Histórica", numbered="②"))
if trend is not None and not trend.empty and len(trend) >= 2:
    fig_trend = px.bar(
        trend.melt(id_vars="ano", value_vars=["empenhado", "pago"], var_name="Tipo", value_name="Valor"),
        x="ano",
        y="Valor",
        color="Tipo",
        barmode="group",
        labels={"ano": "Ano", "Valor": "R$", "Tipo": ""},
        color_discrete_map={"empenhado": "oklch(0.52 0.13 250)", "pago": "oklch(0.35 0.1 250)"},
    )
    fig_trend.for_each_trace(lambda t: t.update(name="Empenhado" if t.name == "empenhado" else "Pago"))
    fig_trend.update_traces(hovertemplate="%{x}<br>R$ %{y:,.0f}<extra></extra>", marker_line_width=0)
    fig_trend.update_layout(
        **plotly_card_layout("Repasses ao CAPREM por Ano", height=300),
        yaxis=dict(tickprefix="R$ ", tickformat=",.0f"),
        xaxis=dict(tickangle=0, type="category"),
    )
    st.html(plotly_card_start())
    st.plotly_chart(fig_trend, use_container_width=True)
    st.html(plotly_card_end())
else:
    st.info("Sem dados históricos disponíveis.")

# ── Por Entidade ─────────────────────────────────────────────────────────────
st.html(section_heading("Por Entidade", numbered="③"))
entidades = data.get("entidades")
if entidades is not None and not entidades.empty:
    _ent_rows = [
        (str(r["entidade"]), float(r["empenhado"]), fmt_compact(float(r["empenhado"])))
        for _, r in entidades.sort_values("empenhado", ascending=False).head(8).iterrows()
    ]
    st.html(bar_chart_h(_ent_rows))

    st.dataframe(
        entidades[["entidade", "empenhado", "liquidado", "pago"]].rename(
            columns={"entidade": "Entidade", "empenhado": "Empenhado", "liquidado": "Liquidado", "pago": "Pago"}
        ),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Liquidado": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
        },
    )
else:
    st.info("Sem dados de entidades para este ano.")

# ── Por Função de Governo ────────────────────────────────────────────────────
st.html(section_heading("Por Função de Governo", numbered="④"))
funcoes = data.get("funcoes")
if funcoes is not None and not funcoes.empty:
    _func_totals = funcoes.groupby("funcao_nome")["empenhado"].sum().sort_values(ascending=False)
    _func_rows = [(str(fn), float(val), fmt_compact(float(val))) for fn, val in _func_totals.head(8).items()]
    st.html(bar_chart_h(_func_rows))

    st.dataframe(
        funcoes.sort_values(["funcao_nome", "empenhado", "subfuncao_nome"], ascending=[True, False, True]).rename(
            columns={
                "funcao_nome": "Função",
                "subfuncao_nome": "Subfunção",
                "empenhado": "Empenhado",
                "pago": "Pago",
            }
        ),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
        },
    )
else:
    st.info("Sem dados por função para este ano.")

# ── Distribuição Mensal ──────────────────────────────────────────────────────
st.html(section_heading("Distribuição Mensal", numbered="⑤"))
mensal = data.get("mensal")
if mensal is not None and not mensal.empty:
    mensal = mensal.copy()
    mensal["mes_nome"] = mensal["mes"].astype(str).str.zfill(2).map(_MESES_PT).fillna(mensal["mes"])
    fig_mensal = px.bar(
        mensal.melt(id_vars="mes_nome", value_vars=["empenhado", "pago"], var_name="Tipo", value_name="Valor"),
        x="mes_nome",
        y="Valor",
        color="Tipo",
        barmode="group",
        labels={"mes_nome": "Mês", "Valor": "R$", "Tipo": ""},
        color_discrete_map={"empenhado": "oklch(0.52 0.13 250)", "pago": "oklch(0.35 0.1 250)"},
        category_orders={"mes_nome": list(_MESES_PT.values())},
    )
    fig_mensal.for_each_trace(lambda t: t.update(name="Empenhado" if t.name == "empenhado" else "Pago"))
    fig_mensal.update_traces(hovertemplate="%{x}<br>R$ %{y:,.0f}<extra></extra>", marker_line_width=0)
    fig_mensal.update_layout(
        **plotly_card_layout(f"Repasses Mensais — {year}", height=280),
        yaxis=dict(tickprefix="R$ ", tickformat=",.0f"),
        xaxis=dict(tickangle=0),
    )
    st.html(plotly_card_start())
    st.plotly_chart(fig_mensal, use_container_width=True)
    st.html(plotly_card_end())
else:
    st.info("Sem dados mensais para este ano.")

# ── Natureza do Repasse ──────────────────────────────────────────────────────
st.html(section_heading("Natureza do Repasse", numbered="⑥"))
natureza = data.get("natureza")
if natureza is not None and not natureza.empty:
    st.dataframe(
        natureza[["descricao", "natureza", "empenhado"]].rename(
            columns={"descricao": "Elemento", "natureza": "Natureza", "empenhado": "Empenhado"}
        ),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
        },
    )
else:
    st.info("Sem dados de natureza para este ano.")

st.caption(f"Fonte: [Portal de Transparência]({constants.PORTAL_URL})")
