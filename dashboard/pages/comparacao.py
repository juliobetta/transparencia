import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import (
    YEARS,
    comparison_table,
    fmt_currency,
    fmt_delta,
    fmt_percent,
    get_conn,
    get_extraction_date,
    render_partial_year_notice,
    render_revenue_methodology,
    render_sidebar,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import comparison
from analysis.comparison import PeriodSpec

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _comparison(conn, spec_a, spec_b, _extracted_at):
    return comparison.run(conn, spec_a, spec_b)


conn = get_conn()
_extracted_at = get_extraction_date(conn)
render_sidebar()  # sidebar portal link + metadata; year value not used on this page

st.header("Comparação de Períodos")
st.caption("Compare dois períodos e veja as variações em cada dimensão.")

MONTHS = list(range(1, 13))
MONTH_NAMES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Período A")
    year_a = st.selectbox("Ano A", YEARS, index=0, key="cmp_year_a")
    m_start_a = st.selectbox("Mês início A", MONTHS, index=0, format_func=lambda m: MONTH_NAMES[m - 1], key="cmp_ms_a")
    m_end_a = st.selectbox("Mês fim A", MONTHS, index=11, format_func=lambda m: MONTH_NAMES[m - 1], key="cmp_me_a")
with col_b:
    st.subheader("Período B")
    year_b = st.selectbox("Ano B", YEARS, index=len(YEARS) - 2, key="cmp_year_b")
    m_start_b = st.selectbox("Mês início B", MONTHS, index=0, format_func=lambda m: MONTH_NAMES[m - 1], key="cmp_ms_b")
    m_end_b = st.selectbox("Mês fim B", MONTHS, index=11, format_func=lambda m: MONTH_NAMES[m - 1], key="cmp_me_b")

spec_a = PeriodSpec(year=year_a, month_start=m_start_a, month_end=m_end_a)
spec_b = PeriodSpec(year=year_b, month_start=m_start_b, month_end=m_end_b)
result = _comparison(conn, spec_a, spec_b, _extracted_at)

st.subheader("Resumo")
m1, m2, m3, m4, m5 = st.columns(5)
d = result["despesas"]["empenhado"]
m1.metric("Empenhado", fmt_currency(d["b"]), delta=fmt_delta(d), delta_color="inverse")
d = result["pessoal"]["percentual_folha"]
m2.metric("Folha / Gastos", fmt_percent(d["b"]), delta=fmt_delta(d, "{:+.1f}%"), delta_color="inverse")
d = result["licitacoes"]["sem_licitacao"]
m3.metric("Sem Licitação", f"{d['b']:.0f}", delta=fmt_delta(d, "{:+.0f}"), delta_color="inverse")
d = result["fornecedores"]["hhi"]
m4.metric("HHI", f"{d['b']:.0f}", delta=fmt_delta(d, "{:+.0f}"), delta_color="inverse")
d = result["adesao"]["count"]
m5.metric("Adesões", f"{d['b']:.0f}", delta=fmt_delta(d, "{:+.0f}"), delta_color="inverse")

with st.expander("Despesas"):
    df = comparison_table(result["despesas"], [("Empenhado", "empenhado"), ("Dotação Atualizada", "dotacao")])
    st.dataframe(
        df,
        column_config={
            "Período A": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Período B": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Δ Absoluto": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Δ %": st.column_config.NumberColumn(format="%.2f%%"),
        },
        width="stretch",
        hide_index=True,
    )
with st.expander("Pessoal"):
    df_currency = comparison_table(result["pessoal"], [("Total Folha", "total_folha")])
    st.dataframe(
        df_currency,
        column_config={
            "Período A": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Período B": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Δ Absoluto": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Δ %": st.column_config.NumberColumn(format="%.2f%%"),
        },
        width="stretch",
        hide_index=True,
    )
    df_percent = comparison_table(result["pessoal"], [("% dos Gastos", "percentual_folha")])
    st.dataframe(
        df_percent,
        column_config={
            "Período A": st.column_config.NumberColumn(format="%.2f%%"),
            "Período B": st.column_config.NumberColumn(format="%.2f%%"),
            "Δ Absoluto": st.column_config.NumberColumn(format="%.2f%%"),
            "Δ %": st.column_config.NumberColumn(format="%.2f%%"),
        },
        width="stretch",
        hide_index=True,
    )
with st.expander("Receitas"):
    render_revenue_methodology()
    if year_a == 2026 or year_b == 2026:
        render_partial_year_notice(2026, _extracted_at)
    df_receitas = comparison_table(
        result["receitas"],
        [
            ("Receita Própria", "receita_propria"),
            ("Transferências da União", "transferencias_uniao"),
            ("Transferências do Estado", "transferencias_estado"),
            ("Total", "total"),
        ],
    )
    st.dataframe(
        df_receitas,
        column_config={
            "Período A": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Período B": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Δ Absoluto": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Δ %": st.column_config.NumberColumn(format="%.2f%%"),
        },
        width="stretch",
        hide_index=True,
    )
with st.expander("Licitações"):
    df = comparison_table(
        result["licitacoes"],
        [
            ("Contratos sem Licitação", "sem_licitacao"),
            ("Acima do Limite Legal", "acima_limite"),
            ("Na Saúde", "saude"),
        ],
    )
    st.dataframe(
        df,
        column_config={
            "Período A": st.column_config.NumberColumn(format="%,.0f"),
            "Período B": st.column_config.NumberColumn(format="%,.0f"),
            "Δ Absoluto": st.column_config.NumberColumn(format="%,.0f"),
            "Δ %": st.column_config.NumberColumn(format="%.2f%%"),
        },
        width="stretch",
        hide_index=True,
    )
with st.expander("Fornecedores"):
    df = comparison_table(result["fornecedores"], [("HHI", "hhi")])
    st.dataframe(
        df,
        column_config={
            "Período A": st.column_config.NumberColumn(format="%,.0f"),
            "Período B": st.column_config.NumberColumn(format="%,.0f"),
            "Δ Absoluto": st.column_config.NumberColumn(format="%,.0f"),
            "Δ %": st.column_config.NumberColumn(format="%.2f%%"),
        },
        width="stretch",
        hide_index=True,
    )

with st.expander("Adesão de Ata"):
    st.subheader("Adesão de Ata")
    df = comparison_table(
        result["adesao"],
        [("Quantidade", "count")],
    )
    st.dataframe(
        df,
        column_config={
            "Período A": st.column_config.NumberColumn(format="%,.0f"),
            "Período B": st.column_config.NumberColumn(format="%,.0f"),
            "Δ Absoluto": st.column_config.NumberColumn(format="%,.0f"),
            "Δ %": st.column_config.NumberColumn(format="%.2f%%"),
        },
        width="stretch",
        hide_index=True,
    )
    df = comparison_table(
        result["adesao"],
        [("Valor Licitação", "valor_licitacao"), ("Valor Contratos", "valor_contratos")],
    )
    st.dataframe(
        df,
        column_config={
            "Período A": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Período B": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Δ Absoluto": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Δ %": st.column_config.NumberColumn(format="%.2f%%"),
        },
        width="stretch",
        hide_index=True,
    )

st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
