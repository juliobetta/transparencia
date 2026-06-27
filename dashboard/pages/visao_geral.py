import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from shared import fmt_currency, fmt_percent, get_conn, render_sidebar

import glossary
from analysis import (
    bidding_gaps,
    budget_execution,
    payroll_vs_services,
    revenue_sources,
    yoy_trends,
)


def _sparkline(x: list, y: list, color: str = "#2196F3") -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy",
        )
    )
    fig.update_layout(
        height=80,
        margin=dict(l=0, r=0, t=4, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


conn = get_conn()
year = render_sidebar()

st.title("Transparência Porciúncula / RJ")
st.caption(f"Dados extraídos do [Portal de Transparência]({glossary.PORTAL_URL}) do município.")
st.header("Visão Geral")

budget = budget_execution.run(conn, year)
bidding = bidding_gaps.run(conn, year)
revenue = revenue_sources.run(conn, [year])
payroll = payroll_vs_services.run(conn, [year])
yoy = yoy_trends.run(conn, list(range(2022, year + 1)))

anos = yoy["ano"].tolist()
_spark_cfg = {"displayModeBar": False, "staticPlot": True}

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    total_gasto = float(yoy.iloc[-1]["total_gasto"]) if not yoy.empty else 0.0
    delta_gasto = yoy.iloc[-1]["total_gasto_pct_change"] if len(yoy) > 1 else None
    st.metric(
        "Total Pago",
        fmt_currency(total_gasto),
        delta=f"{delta_gasto:+.1f}%" if delta_gasto is not None and not pd.isna(delta_gasto) else None,
        delta_color="off",
        help="Valor total liquidado e pago.",
    )
    st.plotly_chart(
        _sparkline(anos, yoy["total_gasto"].tolist()),
        use_container_width=True,
        config=_spark_cfg,
    )

with c2:
    contracts_no_bid = int((bidding["licitacao_numero"].fillna("").str.strip() == "").sum())
    st.metric(
        "Contratos sem licitação",
        contracts_no_bid,
        help=glossary.tooltip("Licitação"),
    )

with c3:
    if not revenue.empty:
        row = revenue.iloc[0]
        label = "Receita Arrecadada" if year == 2026 else "Receita Prevista"
        rev_val = row["total_arrecadado"] if year == 2026 else row["total_previsto"]
        delta_rec = yoy.iloc[-1]["total_receita_pct_change"] if len(yoy) > 1 else None
        help_text = "Total efetivamente arrecadado." if year == 2026 else "Previsão orçamentária do ano."
        st.metric(
            label,
            fmt_currency(float(rev_val)),
            delta=f"{delta_rec:+.1f}%" if delta_rec is not None and not pd.isna(delta_rec) else None,
            help=help_text,
        )
        st.plotly_chart(
            _sparkline(anos, yoy["total_receita"].tolist(), "#4CAF50"),
            use_container_width=True,
            config=_spark_cfg,
        )

with c4:
    if not payroll.empty:
        delta_folha = yoy.iloc[-1]["total_folha_pct_change"] if len(yoy) > 1 else None
        st.metric(
            "Folha / Gastos Totais",
            fmt_percent(payroll.iloc[0]["percentual_folha"]),
            delta=f"{delta_folha:+.1f}%" if delta_folha is not None and not pd.isna(delta_folha) else None,
            delta_color="inverse",
        )
        st.plotly_chart(
            _sparkline(anos, yoy["total_folha"].tolist(), "#FF9800"),
            use_container_width=True,
            config=_spark_cfg,
        )

with c5:
    restos = float(yoy.iloc[-1]["restos_a_pagar"]) if not yoy.empty else 0.0
    delta_restos = yoy.iloc[-1]["restos_a_pagar_pct_change"] if len(yoy) > 1 else None
    st.metric(
        "Restos a Pagar",
        fmt_currency(restos),
        delta=f"{delta_restos:+.1f}%" if delta_restos is not None and not pd.isna(delta_restos) else None,
        delta_color="off",
        help="Restos a pagar efetivamente pagos no ano.",
    )
    st.plotly_chart(
        _sparkline(anos, yoy["restos_a_pagar"].tolist(), "#9C27B0"),
        use_container_width=True,
        config=_spark_cfg,
    )

st.subheader("Tendências Ano a Ano")
st.dataframe(
    yoy.rename(
        columns={
            "ano": "Ano",
            "total_gasto": "Total Pago",
            "total_folha": "Total Folha",
            "total_receita": "Total Receita",
            "restos_a_pagar": "Restos Pago",
            "total_gasto_pct_change": "Δ% Gasto",
            "total_folha_pct_change": "Δ% Folha",
            "total_receita_pct_change": "Δ% Receita",
            "restos_a_pagar_pct_change": "Δ% Restos",
        }
    ),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Total Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
        "Total Folha": st.column_config.NumberColumn(format="R$ %,.2f"),
        "Total Receita": st.column_config.NumberColumn(format="R$ %,.2f"),
        "Restos Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
        "Δ% Gasto": st.column_config.NumberColumn(format="%.2f%%"),
        "Δ% Folha": st.column_config.NumberColumn(format="%.2f%%"),
        "Δ% Receita": st.column_config.NumberColumn(format="%.2f%%"),
        "Δ% Restos": st.column_config.NumberColumn(format="%.2f%%"),
    },
)

st.info(f"🔗 Para informações detalhadas, acesse o portal oficial: [{glossary.PORTAL_URL}]({glossary.PORTAL_URL})")
