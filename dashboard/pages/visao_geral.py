import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import fmt_currency, fmt_percent, get_conn, render_sidebar

import glossary
from analysis import (
    bidding_gaps,
    budget_execution,
    payroll_vs_services,
    revenue_sources,
    supplier_concentration,
    yoy_trends,
)

conn = get_conn()
year = render_sidebar()

st.title("Transparência Porciúncula / RJ")
st.caption(f"Dados extraídos do [Portal de Transparência]({glossary.PORTAL_URL}) do município.")
st.header("Visão Geral")

budget = budget_execution.run(conn, year)
supplier_result = supplier_concentration.run(conn, year)
bidding = bidding_gaps.run(conn, year)
revenue = revenue_sources.run(conn, [year])
payroll = payroll_vs_services.run(conn, [year])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total empenhado", fmt_currency(budget["empenhado"].sum()), help=glossary.tooltip("Empenho"))
c2.metric(
    "Contratos sem licitação",
    int((bidding["licitacao_numero"].fillna("").str.strip() == "").sum()),
    help=glossary.tooltip("Licitação"),
)
if not revenue.empty:
    c3.metric("Receita própria", fmt_percent(revenue.iloc[0]["pct_propria"]), help=glossary.tooltip("Receita Própria"))
if not payroll.empty:
    c4.metric("Folha / gastos totais", fmt_percent(payroll.iloc[0]["percentual_folha"]))

st.subheader("Tendências Ano a Ano")
yoy = yoy_trends.run(conn, list(range(2022, year + 1)))
st.dataframe(
    yoy.rename(
        columns={
            "ano": "Ano",
            "total_gasto": "Total Gasto",
            "total_folha": "Total Folha",
            "total_receita": "Total Receita",
            "restos_a_pagar": "Restos a Pagar",
            "total_gasto_pct_change": "Δ% Gasto",
            "total_folha_pct_change": "Δ% Folha",
            "total_receita_pct_change": "Δ% Receita",
            "restos_a_pagar_pct_change": "Δ% Restos",
        }
    ),
    use_container_width=True,
    column_config={
        "Total Gasto": st.column_config.NumberColumn(format="R$ %,.2f"),
        "Total Folha": st.column_config.NumberColumn(format="R$ %,.2f"),
        "Total Receita": st.column_config.NumberColumn(format="R$ %,.2f"),
        "Restos a Pagar": st.column_config.NumberColumn(format="R$ %,.2f"),
        "Δ% Gasto": st.column_config.NumberColumn(format="%.2f%%"),
        "Δ% Folha": st.column_config.NumberColumn(format="%.2f%%"),
        "Δ% Receita": st.column_config.NumberColumn(format="%.2f%%"),
        "Δ% Restos": st.column_config.NumberColumn(format="%.2f%%"),
    },
)

st.info(f"🔗 Para informações detalhadas, acesse o portal oficial: [{glossary.PORTAL_URL}]({glossary.PORTAL_URL})")
