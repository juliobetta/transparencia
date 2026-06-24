import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import YEARS, comparison_table, fmt_delta, get_conn, render_sidebar

import glossary
from analysis import comparison
from analysis.comparison import PeriodSpec

conn = get_conn()
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
result = comparison.run(conn, spec_a, spec_b)

st.subheader("Resumo")
m1, m2, m3, m4, m5 = st.columns(5)
d = result["despesas"]["empenhado"]
m1.metric("Empenhado (R$)", f"{d['b']:,.0f}", delta=fmt_delta(d), delta_color="inverse")
d = result["pessoal"]["percentual_folha"]
m2.metric("Folha / Gastos", f"{d['b']:.1f}%", delta=fmt_delta(d, "{:+.1f}%"), delta_color="inverse")
d = result["licitacoes"]["sem_licitacao"]
m3.metric("Sem Licitação (Irregular)", f"{d['b']:.0f}", delta=fmt_delta(d, "{:+.0f}"), delta_color="inverse")
d = result["fornecedores"]["hhi"]
m4.metric("HHI", f"{d['b']:,.0f}", delta=fmt_delta(d), delta_color="inverse")
d = result["adesao"]["count"]
m5.metric("Adesões", f"{d['b']:.0f}", delta=fmt_delta(d, "{:+.0f}"), delta_color="inverse")

with st.expander("Despesas"):
    st.dataframe(
        comparison_table(
            result["despesas"], [("Empenhado (R$)", "empenhado"), ("Dotação Atualizada (R$)", "dotacao")], "{:,.0f}"
        ),
        use_container_width=True,
    )
with st.expander("Pessoal"):
    st.dataframe(
        comparison_table(
            result["pessoal"], [("Total Folha (R$)", "total_folha"), ("% dos Gastos", "percentual_folha")], "{:.2f}"
        ),
        use_container_width=True,
    )
with st.expander("Licitações"):
    st.dataframe(
        comparison_table(
            result["licitacoes"],
            [
                ("Contratos sem Licitação (Irregular)", "sem_licitacao"),
                ("Acima do Limite Legal", "acima_limite"),
                ("Na Saúde", "saude"),
            ],
            "{:.0f}",
        ),
        use_container_width=True,
    )
with st.expander("Fornecedores"):
    st.dataframe(comparison_table(result["fornecedores"], [("HHI", "hhi")], "{:,.0f}"), use_container_width=True)

with st.expander("Adesão de Ata"):
    st.dataframe(
        comparison_table(
            result["adesao"],
            [("Quantidade", "count"), ("Valor Licitação", "valor_licitacao"), ("Valor Contratos", "valor_contratos")],
            "{:,.0f}",
        ),
        use_container_width=True,
    )

st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
