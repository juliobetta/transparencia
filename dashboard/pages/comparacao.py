import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import (
    ANO_ATUAL,
    ANOS,
    comparison_table,
    fmt_currency,
    fmt_delta,
    fmt_percent,
    get_conn,
    get_data_extracao,
    render_aviso_ano_parcial,
    render_metodologia_receita,
    render_sidebar,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import comparacao
from analysis.comparacao import PeriodSpec

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _comparacao(conn, periodo_a, periodo_b, _extracted_at):
    return comparacao.run(conn, periodo_a, periodo_b)


conn = get_conn()
_extracted_at = get_data_extracao(conn)
_, _ = render_sidebar()  # sidebar com entidade e ano; valores ignorados nesta página

st.header("Comparação de Períodos")
st.caption("Compare dois períodos e veja as variações em cada dimensão.")

MESES = list(range(1, 13))
NOMES_MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

col_periodo_a, col_periodo_b = st.columns(2)
with col_periodo_a:
    st.subheader("Período A")
    ano_a = st.selectbox("Ano A", ANOS, index=0, key="cmp_year_a")
    mes_inicio_a = st.selectbox(
        "Mês início A", MESES, index=0, format_func=lambda m: NOMES_MESES[m - 1], key="cmp_ms_a"
    )
    mes_fim_a = st.selectbox("Mês fim A", MESES, index=11, format_func=lambda m: NOMES_MESES[m - 1], key="cmp_me_a")
with col_periodo_b:
    st.subheader("Período B")
    ano_b = st.selectbox("Ano B", ANOS, index=len(ANOS) - 2, key="cmp_year_b")
    mes_inicio_b = st.selectbox(
        "Mês início B", MESES, index=0, format_func=lambda m: NOMES_MESES[m - 1], key="cmp_ms_b"
    )
    mes_fim_b = st.selectbox("Mês fim B", MESES, index=11, format_func=lambda m: NOMES_MESES[m - 1], key="cmp_me_b")

periodo_a = PeriodSpec(year=ano_a, mes_inicio=mes_inicio_a, mes_fim=mes_fim_a)
periodo_b = PeriodSpec(year=ano_b, mes_inicio=mes_inicio_b, mes_fim=mes_fim_b)
resultado = _comparacao(conn, periodo_a, periodo_b, _extracted_at)

st.subheader("Resumo")
m1, m2, m3, m4, m5 = st.columns(5)
dado = resultado["despesas"]["empenhado"]
m1.metric("Empenhado", fmt_currency(dado["b"]), delta=fmt_delta(dado), delta_color="inverse")
dado = resultado["pessoal"]["percentual_folha"]
m2.metric("Folha / Total Pago", fmt_percent(dado["b"]), delta=fmt_delta(dado, "{:+.1f}%"), delta_color="inverse")
dado = resultado["licitacoes"]["sem_licitacao"]
m3.metric("Sem Licitação", f"{dado['b']:.0f}", delta=fmt_delta(dado, "{:+.0f}"), delta_color="inverse")
dado = resultado["fornecedores"]["hhi"]
m4.metric("HHI", f"{dado['b']:.0f}", delta=fmt_delta(dado, "{:+.0f}"), delta_color="inverse")
dado = resultado["adesao"]["quantidade"]
m5.metric("Adesões", f"{dado['b']:.0f}", delta=fmt_delta(dado, "{:+.0f}"), delta_color="inverse")

with st.expander("Despesas"):
    df = comparison_table(resultado["despesas"], [("Empenhado", "empenhado"), ("Dotação Atualizada", "dotacao")])
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
    df_moeda = comparison_table(resultado["pessoal"], [("Total Folha", "total_folha")])
    st.dataframe(
        df_moeda,
        column_config={
            "Período A": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Período B": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Δ Absoluto": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Δ %": st.column_config.NumberColumn(format="%.2f%%"),
        },
        width="stretch",
        hide_index=True,
    )
    df_porcentagem = comparison_table(resultado["pessoal"], [("% do Total Pago", "percentual_folha")])
    st.dataframe(
        df_porcentagem,
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
    render_metodologia_receita()
    if ano_a == ANO_ATUAL or ano_b == ANO_ATUAL:
        render_aviso_ano_parcial(ANO_ATUAL, _extracted_at)
    df_receitas = comparison_table(
        resultado["receitas"],
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
        resultado["licitacoes"],
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
    df = comparison_table(resultado["fornecedores"], [("HHI", "hhi")])
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
        resultado["adesao"],
        [("Quantidade", "quantidade")],
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
        resultado["adesao"],
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
