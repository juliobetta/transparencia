import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from shared import (
    fmt_percent,
    get_conn,
    get_extraction_date,
    render_partial_year_notice,
    render_revenue_methodology,
    render_sidebar,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import (
    adesao_de_ata,
    bidding_gaps,
    budget_execution,
    contract_anomalies,
    fiscal_position,
    payroll_vs_services,
    revenue_sources,
    yoy_trends,
)

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _budget(conn, year, _extracted_at):
    return budget_execution.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _bidding(conn, year, _extracted_at):
    return bidding_gaps.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _bidding_counts(conn, years, _extracted_at):
    return bidding_gaps.counts_by_year(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _revenue(conn, years, _extracted_at):
    return revenue_sources.run(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _payroll(conn, years, _extracted_at):
    return payroll_vs_services.run(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _yoy(conn, years, _extracted_at):
    return yoy_trends.run(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_counts(conn, years, _extracted_at):
    return adesao_de_ata.formal_counts_by_year(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_externa_counts(conn, years, _extracted_at):
    return adesao_de_ata.external_counts_by_year(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _splitting_counts(conn, years, _extracted_at):
    return contract_anomalies.splitting_counts_by_year(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _unpaid_suppliers(conn, year, _extracted_at):
    return fiscal_position.get_unpaid_suppliers(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _unpaid_trend(conn, years, _extracted_at):
    return fiscal_position.get_unpaid_suppliers_trend(conn, years)


def _pct_delta(series: list) -> str | None:
    if len(series) >= 2 and series[-2] != 0:
        return f"{(series[-1] - series[-2]) / series[-2] * 100:+.1f}%"
    return None


def _fmt_compact(value: float) -> str:
    if abs(value) >= 1_000_000_000:
        return f"R$ {value / 1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:.1f}K"
    return f"R$ {value:.0f}"


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
_extracted_at = get_extraction_date(conn)

st.title("Transparência Porciúncula / RJ")
st.caption(f"Dados extraídos do [Portal de Transparência]({glossary.PORTAL_URL}) do município.")
st.header("Visão Geral")

_all_years = list(range(2022, year + 1))
with st.spinner("Carregando..."):
    budget = _budget(conn, year, _extracted_at)
    bidding = _bidding(conn, year, _extracted_at)
    revenue = _revenue(conn, _all_years, _extracted_at)
    payroll = _payroll(conn, [year], _extracted_at)
    yoy = _yoy(conn, _all_years, _extracted_at)
    _adesao_map = _adesao_counts(conn, _all_years, _extracted_at)
    _adesao_ext_map = _adesao_externa_counts(conn, _all_years, _extracted_at)
    _splitting_map = _splitting_counts(conn, _all_years, _extracted_at)
    unpaid_df = _unpaid_suppliers(conn, year, _extracted_at)
    unpaid_trend = _unpaid_trend(conn, tuple(_all_years), _extracted_at)

anos = yoy["ano"].tolist()
_spark_cfg = {"displayModeBar": False, "staticPlot": True}
_counts_map = _bidding_counts(conn, anos, _extracted_at)
_contract_counts = [_counts_map[y] for y in anos]

c1, c2, c3, c4 = st.columns(4)

with c1:
    total_gasto = float(yoy.iloc[-1]["total_gasto"]) if not yoy.empty else 0.0
    delta_gasto = yoy.iloc[-1]["total_gasto_pct_change"] if len(yoy) > 1 else None
    st.metric(
        "Total Pago",
        _fmt_compact(total_gasto),
        delta=f"{delta_gasto:+.1f}%" if delta_gasto is not None and not pd.isna(delta_gasto) else None,
        delta_color="off",
        help="Valor total liquidado e pago.",
    )
    st.plotly_chart(
        _sparkline(anos, yoy["total_gasto"].tolist()),
        use_container_width=True,
        config=_spark_cfg,
        key="spark_total_gasto",
    )

with c2:
    if not revenue.empty:
        row = revenue[revenue["ano"] == year].iloc[0] if year in revenue["ano"].values else revenue.iloc[-1]
        label = "Receita Arrecadada" if year == 2026 else "Receita Prevista"
        rev_val = row["total_arrecadado"] if year == 2026 else row["total_previsto"]
        _rev_totals = revenue["total"].tolist()
        delta_rec = (
            (_rev_totals[-1] - _rev_totals[-2]) / _rev_totals[-2] * 100
            if len(_rev_totals) > 1 and _rev_totals[-2] != 0
            else None
        )
        help_text = "Total efetivamente arrecadado." if year == 2026 else "Previsão orçamentária do ano."
        st.metric(
            label,
            _fmt_compact(float(rev_val)),
            delta=f"{delta_rec:+.1f}%" if delta_rec is not None and not pd.isna(delta_rec) else None,
            help=help_text,
        )
        st.plotly_chart(
            _sparkline(anos, revenue["total"].tolist(), "#4CAF50"),
            use_container_width=True,
            config=_spark_cfg,
            key="spark_receita",
        )

with c3:
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
            key="spark_folha",
        )

with c4:
    restos = float(yoy.iloc[-1]["restos_a_pagar"]) if not yoy.empty else 0.0
    delta_restos = yoy.iloc[-1]["restos_a_pagar_pct_change"] if len(yoy) > 1 else None
    st.metric(
        "Restos Pagos",
        _fmt_compact(restos),
        delta=f"{delta_restos:+.1f}%" if delta_restos is not None and not pd.isna(delta_restos) else None,
        delta_color="off",
        help="Restos a pagar efetivamente pagos no ano.",
    )
    st.plotly_chart(
        _sparkline(anos, yoy["restos_a_pagar"].tolist(), "#9C27B0"),
        use_container_width=True,
        config=_spark_cfg,
        key="spark_restos",
    )

st.subheader("Licitações e Contratos")
_bidding_counts_list = [_counts_map[y] for y in anos]
_adesao_counts_list = [_adesao_map[y] for y in anos]
_adesao_ext_counts_list = [_adesao_ext_map[y] for y in anos]
_splitting_counts_list = [_splitting_map[y] for y in anos]

lc1, lc2, lc3, lc4 = st.columns(4)

with lc1:
    contracts_no_bid = int(bidding["acima_limite"].sum())
    _delta_contracts = (
        (_contract_counts[-1] - _contract_counts[-2]) / _contract_counts[-2] * 100
        if len(_contract_counts) > 1 and _contract_counts[-2] != 0
        else None
    )
    st.metric(
        "Acima do limite s/ licitação",
        contracts_no_bid,
        delta=f"{_delta_contracts:+.1f}%" if _delta_contracts is not None else None,
        delta_color="inverse",
        help="Contratos sem licitação acima de R$ 62.725,59 (bens e serviços). [Lei 14.133/21, Art. 75, I](https://licitacoesecontratos.tcu.gov.br/5-10-2-1-dispensa-em-razao-do-valor-incisos-i-e-ii-2/)",
    )
    st.plotly_chart(
        _sparkline(anos, _bidding_counts_list, "#E91E63"),
        use_container_width=True,
        config=_spark_cfg,
        key="spark_lc_acima",
    )

with lc2:
    _delta_adesao = (
        (_adesao_counts_list[-1] - _adesao_counts_list[-2]) / _adesao_counts_list[-2] * 100
        if len(_adesao_counts_list) > 1 and _adesao_counts_list[-2] != 0
        else None
    )
    st.metric(
        "Adesões de Ata (formal)",
        _adesao_map[year],
        delta=f"{_delta_adesao:+.1f}%" if _delta_adesao is not None else None,
        delta_color="inverse",
        help=glossary.tooltip("Adesão de Ata (Carona)"),
    )
    st.plotly_chart(
        _sparkline(anos, _adesao_counts_list, "#FF9800"),
        use_container_width=True,
        config=_spark_cfg,
        key="spark_lc_adesao",
    )

with lc3:
    _delta_ext = (
        (_adesao_ext_counts_list[-1] - _adesao_ext_counts_list[-2]) / _adesao_ext_counts_list[-2] * 100
        if len(_adesao_ext_counts_list) > 1 and _adesao_ext_counts_list[-2] != 0
        else None
    )
    st.metric(
        "Empenhos via Ata Externa",
        _adesao_ext_map[year],
        delta=f"{_delta_ext:+.1f}%" if _delta_ext is not None else None,
        delta_color="inverse",
        help="Empenhos cuja justificativa contábil referencia um Termo de Adesão Externa a Ata de Registro de Preços de outro ente.",
    )
    st.plotly_chart(
        _sparkline(anos, _adesao_ext_counts_list, "#9C27B0"),
        use_container_width=True,
        config=_spark_cfg,
        key="spark_lc_ext",
    )

with lc4:
    _delta_split = (
        (_splitting_counts_list[-1] - _splitting_counts_list[-2]) / _splitting_counts_list[-2] * 100
        if len(_splitting_counts_list) > 1 and _splitting_counts_list[-2] != 0
        else None
    )
    st.metric(
        "Possível fracionamento",
        _splitting_map[year],
        delta=f"{_delta_split:+.1f}%" if _delta_split is not None else None,
        delta_color="inverse",
        help="Contratos do mesmo fornecedor com valores próximos ao limite de dispensa (R$ 62.725,59), sugerindo possível fracionamento.",
    )
    st.plotly_chart(
        _sparkline(anos, _splitting_counts_list, "#F44336"),
        use_container_width=True,
        config=_spark_cfg,
        key="spark_lc_split",
    )

if not unpaid_df.empty:
    total_pendente = unpaid_df["pendente"].sum()
    num_fornecedores = len(unpaid_df)
    ano_mais_antigo = int(unpaid_df["aguardando_desde"].min())

    _trend_vals = unpaid_trend["total_pendente"].tolist() if not unpaid_trend.empty else []
    _trend_count = unpaid_trend["num_fornecedores"].tolist() if not unpaid_trend.empty else []
    _trend_anos = unpaid_trend["ano"].tolist() if not unpaid_trend.empty else []

    st.subheader("Restos a Pagar — Obrigações Pendentes")
    rp1, rp2, rp3 = st.columns(3)

    with rp1:
        st.metric(
            "Total a Pagar a Fornecedores",
            _fmt_compact(total_pendente),
            delta=_pct_delta(_trend_vals),
            delta_color="inverse",
            help="Soma de todos os empenhos ainda não quitados na tabela de Restos a Pagar.",
        )
        if _trend_vals:
            st.plotly_chart(
                _sparkline(_trend_anos, _trend_vals, "#E91E63"),
                use_container_width=True,
                config=_spark_cfg,
                key="spark_rp_total",
            )

    with rp2:
        st.metric(
            "Fornecedores aguardando",
            num_fornecedores,
            delta=_pct_delta(_trend_count),
            delta_color="inverse",
            help="Número de fornecedores com pelo menos um empenho não totalmente pago.",
        )
        if _trend_count:
            st.plotly_chart(
                _sparkline(_trend_anos, _trend_count, "#FF5722"),
                use_container_width=True,
                config=_spark_cfg,
                key="spark_rp_count",
            )

    with rp3:
        st.metric(
            "Dívida mais antiga desde",
            str(ano_mais_antigo),
            help="Exercício do empenho mais antigo ainda com saldo pendente.",
        )

    st.info(
        "Detalhamento completo por fornecedor disponível em **Despesas → Restos a Pagar**.",
        icon=":material/info:",
    )

st.subheader("Tendências Históricas")
col_trend, col_pct = st.columns([6, 4])

with col_trend:
    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=anos,
            y=yoy["total_gasto"].tolist(),
            name="Total Pago",
            mode="lines+markers",
            line=dict(color="#2196F3", width=2),
            fill="tozeroy",
        )
    )
    fig_trend.add_trace(
        go.Scatter(
            x=anos,
            y=yoy["total_receita"].tolist(),
            name="Receita",
            mode="lines+markers",
            line=dict(color="#4CAF50", width=2),
            fill="tozeroy",
        )
    )
    fig_trend.add_trace(
        go.Scatter(
            x=anos,
            y=yoy["total_folha"].tolist(),
            name="Folha",
            mode="lines+markers",
            line=dict(color="#FF9800", width=2),
            fill="tozeroy",
        )
    )
    fig_trend.update_layout(
        title="Evolução Anual (R$)",
        xaxis=dict(dtick=1, tickformat="d"),
        yaxis=dict(tickformat=",.0f", tickprefix="R$ "),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        margin=dict(l=0, r=0, t=40, b=60),
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    st.caption(
        "Gasto crescendo acima da receita é sinal de desequilíbrio fiscal. Folha persistente acima de 60% do gasto total indica rigidez orçamentária — pouco sobra para investimentos."
    )

with col_pct:
    yoy_pct = yoy.dropna(subset=["total_gasto_pct_change", "total_receita_pct_change"]).copy()
    yoy_pct = yoy_pct.replace([float("inf"), float("-inf")], float("nan"))
    yoy_pct = yoy_pct.dropna(subset=["total_gasto_pct_change", "total_receita_pct_change"])
    gap = (yoy_pct["total_gasto_pct_change"] - yoy_pct["total_receita_pct_change"]).tolist()
    colors = ["#F44336" if v > 0 else "#4CAF50" for v in gap]
    fig_pct = go.Figure(
        go.Bar(
            x=yoy_pct["ano"].tolist(),
            y=gap,
            marker_color=colors,
            hovertemplate="%{x}<br>Pressão: %{y:+.1f}%<extra></extra>",
        )
    )
    fig_pct.add_hline(y=0, line_width=1, line_color="rgba(0,0,0,0.3)")
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
        "Barras acima do zero indicam que o gasto cresceu mais do que a receita naquele ano — sinal de pressão fiscal."
    )

render_revenue_methodology()

st.subheader(f"Composição e Execução ({year})")
col_donut, col_bar = st.columns([4, 6])

with col_donut:
    if not revenue.empty:
        row = revenue[revenue["ano"] == year].iloc[0] if year in revenue["ano"].values else revenue.iloc[-1]
        is_partial = year == 2026
        donut_title = (
            f"Fontes de Receita ({year} — Arrecadado Parcial)"
            if is_partial
            else f"Fontes de Receita ({year} — Previsão Orçamentária)"
        )
        fig_donut = go.Figure(
            go.Pie(
                labels=["Receita Própria", "Transferências União", "Transferências Estado"],
                values=[
                    float(row["receita_propria"]),
                    float(row["transferencias_uniao"]),
                    float(row["transferencias_estado"]),
                ],
                hole=0.5,
                marker=dict(colors=["#2196F3", "#4CAF50", "#FF9800"]),
                textinfo="percent+label",
                hovertemplate="%{label}<br>R$ %{value:,.0f}<br>%{percent}<extra></extra>",
            )
        )
        fig_donut.update_layout(
            title=donut_title,
            showlegend=False,
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        if is_partial:
            _prev_rows = revenue[revenue["ano"] == year - 1]
            _propria_cur = _fmt_compact(float(row["receita_propria_previsto"]))
            _propria_prev = (
                _fmt_compact(float(_prev_rows.iloc[0]["receita_propria_previsto"])) if not _prev_rows.empty else "N/D"
            )
            _pct_cur = float(row["pct_propria"])
            _pct_prev = float(_prev_rows.iloc[0]["pct_propria"]) if not _prev_rows.empty else 0
            render_partial_year_notice(
                year,
                _extracted_at,
                extra_html=(
                    f"O salto de ~{_pct_prev:.0f}% ({year - 1}) para ~{_pct_cur:.0f}% ({year}) reflete também uma mudança na "
                    f"previsão orçamentária: a receita própria foi orçada em {_propria_cur} em {year}, frente a {_propria_prev} em {year - 1}."
                ),
            )
        else:
            st.caption(
                "Alta dependência de transferências federais e estaduais fragiliza o município diante de mudanças na política fiscal nacional. Receita própria elevada indica maior autonomia."
            )
    else:
        st.info("Dados de receita não disponíveis.")

with col_bar:
    _alerta_colors = {
        "normal": "#2196F3",
        "baixa": "#FF9800",
        "excesso": "#F44336",
        "N/D": "#9E9E9E",
    }
    by_organ = budget.groupby(["empresa", "descricao"], as_index=False).agg(
        empenhado=("empenhado", "sum"), dotacao_atualizada=("dotacao_atualizada", "sum")
    )
    by_organ["taxa_execucao"] = by_organ.apply(
        lambda r: r["empenhado"] / r["dotacao_atualizada"] if r["dotacao_atualizada"] > 0 else 0.0,
        axis=1,
    )
    by_organ["alerta"] = by_organ.apply(
        lambda r: (
            "N/D"
            if r["empenhado"] == 0 and r["dotacao_atualizada"] == 0
            else ("baixa" if r["taxa_execucao"] < 0.3 else ("excesso" if r["taxa_execucao"] > 1.0 else "normal"))
        ),
        axis=1,
    )
    top10 = by_organ.nlargest(10, "dotacao_atualizada").copy()
    top10["descricao_short"] = top10["descricao"].str[:30]
    top10["bar_color"] = top10["alerta"].map(_alerta_colors).fillna("#9E9E9E")

    fig_bar = go.Figure()
    fig_bar.add_trace(
        go.Bar(
            y=top10["descricao_short"].tolist(),
            x=top10["dotacao_atualizada"].tolist(),
            name="Dotação Atualizada",
            orientation="h",
            marker_color="#E0E0E0",
        )
    )
    fig_bar.add_trace(
        go.Bar(
            y=top10["descricao_short"].tolist(),
            x=top10["empenhado"].tolist(),
            name="Empenhado",
            orientation="h",
            marker_color=top10["bar_color"].tolist(),
        )
    )
    fig_bar.update_layout(
        title=f"Execução Orçamentária — Top 10 Órgãos ({year})",
        barmode="overlay",
        xaxis=dict(tickformat=",.0f", tickprefix="R$ "),
        yaxis=dict(autorange="reversed"),
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        margin=dict(l=0, r=0, t=40, b=60),
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    st.caption(
        "Execução abaixo de 30% pode indicar planejamento deficiente ou projetos paralisados. Acima de 100% aponta dotação insuficiente — ambos são alertas de gestão orçamentária."
    )

with st.expander(":material/bar_chart: Dados detalhados por ano"):
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

st.info(
    f":material/link: Para informações detalhadas, acesse o portal oficial: [{glossary.PORTAL_URL}]({glossary.PORTAL_URL})"
)
