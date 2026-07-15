import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import (
    ANO_ATUAL,
    SPARK_CFG,
    fmt_compact,
    get_conn,
    get_data_extracao,
    pct_delta,
    render_aviso_ano_parcial,
    render_sidebar,
    sparkline,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import historia_caprem
from report.caprem import generate

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

col_titulo, col_botao = st.columns([8, 2])
with col_titulo:
    st.title(f"CAPREM (Caixa de Previdência Municipal) - {year}")
    st.caption(f"Dados do CAPREM extraídos do [Portal de Transparência]({glossary.PORTAL_URL}).")
with col_botao:
    st.write("")
    st.write("")
    pdf_bytes = _pdf(conn, year, _extracted_at)
    st.download_button(
        label="⬇ Baixar PDF",
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
st.header("① Repasses")
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "Total Empenhado",
        fmt_compact(data.get("total_transferencias", 0)),
        delta=pct_delta(_emp_serie),
        delta_color="off",
    )
    if len(_emp_serie) >= 2:
        st.plotly_chart(sparkline(_all_years, _emp_serie), use_container_width=True, config=SPARK_CFG, key="spark_emp")

with k2:
    st.metric(
        "Total Liquidado",
        fmt_compact(data.get("total_liquidado", 0)),
        delta=pct_delta(_liq_serie),
        delta_color="off",
    )
    if len(_liq_serie) >= 2:
        st.plotly_chart(
            sparkline(_all_years, _liq_serie, "#4CAF50"), use_container_width=True, config=SPARK_CFG, key="spark_liq"
        )

with k3:
    st.metric(
        "Total Pago",
        fmt_compact(data.get("total_pago", 0)),
        delta=pct_delta(_pago_serie),
        delta_color="off",
    )
    if len(_pago_serie) >= 2:
        st.plotly_chart(
            sparkline(_all_years, _pago_serie, "#FF9800"), use_container_width=True, config=SPARK_CFG, key="spark_pago"
        )

with k4:
    st.metric("Taxa de Pagamento", f"{data.get('taxa_execucao', 0):.1%}")

st.divider()

# ── Tendência histórica ──────────────────────────────────────────────────────
st.header("② Tendência Histórica")
if trend is not None and not trend.empty and len(trend) >= 2:
    fig_trend = px.bar(
        trend.melt(id_vars="ano", value_vars=["empenhado", "pago"], var_name="Tipo", value_name="Valor"),
        x="ano",
        y="Valor",
        color="Tipo",
        barmode="group",
        labels={"ano": "Ano", "Valor": "R$", "Tipo": ""},
        color_discrete_map={"empenhado": "#3A7FC1", "pago": "#1C3A5E"},
        title="Repasses ao CAPREM por Ano",
    )
    fig_trend.for_each_trace(lambda t: t.update(name="Empenhado" if t.name == "empenhado" else "Pago"))
    fig_trend.update_traces(hovertemplate="%{x}<br>R$ %{y:,.0f}<extra></extra>")
    fig_trend.update_layout(
        yaxis=dict(tickprefix="R$ ", tickformat=",.0f"),
        xaxis=dict(tickangle=0, type="category"),
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("Sem dados históricos disponíveis.")

st.divider()

# ── Por Entidade ─────────────────────────────────────────────────────────────
st.header("③ Por Entidade")
entidades = data.get("entidades")
if entidades is not None and not entidades.empty:
    fig_ent = px.bar(
        entidades,
        x="entidade",
        y="empenhado",
        labels={"entidade": "Entidade", "empenhado": "Empenhado (R$)"},
        title=f"Repasses por Entidade — {year}",
        color_discrete_sequence=["#3A7FC1"],
    )
    fig_ent.update_traces(hovertemplate="%{x}<br>R$ %{y:,.0f}<extra></extra>")
    fig_ent.update_layout(
        yaxis=dict(tickprefix="R$ ", tickformat=",.0f"),
        xaxis=dict(tickangle=0),
    )
    st.plotly_chart(fig_ent, use_container_width=True)

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

st.divider()

# ── Por Função de Governo ────────────────────────────────────────────────────
st.header("④ Por Função de Governo")
funcoes = data.get("funcoes")
if funcoes is not None and not funcoes.empty:
    _func_order = funcoes.groupby("funcaonome")["empenhado"].sum().sort_values(ascending=False).index.tolist()
    fig_func = px.bar(
        funcoes,
        x="funcaonome",
        y="empenhado",
        color="subfuncaonome",
        labels={"funcaonome": "Função", "empenhado": "Empenhado (R$)", "subfuncaonome": "Subfunção"},
        title=f"Repasses por Função de Governo — {year}",
        category_orders={"funcaonome": _func_order},
    )
    fig_func.update_traces(hovertemplate="%{fullData.name}<br>R$ %{y:,.0f}<extra></extra>")
    fig_func.update_layout(
        yaxis=dict(tickprefix="R$ ", tickformat=",.0f"),
        xaxis=dict(tickangle=0),
        showlegend=False,
    )
    st.plotly_chart(fig_func, use_container_width=True)

    st.dataframe(
        funcoes.sort_values(["funcaonome", "empenhado", "subfuncaonome"], ascending=[True, False, True]).rename(
            columns={
                "funcaonome": "Função",
                "subfuncaonome": "Subfunção",
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

st.divider()

# ── Distribuição Mensal ──────────────────────────────────────────────────────
st.header("⑤ Distribuição Mensal")
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
        color_discrete_map={"empenhado": "#3A7FC1", "pago": "#1C3A5E"},
        title=f"Repasses Mensais — {year}",
        category_orders={"mes_nome": list(_MESES_PT.values())},
    )
    fig_mensal.for_each_trace(lambda t: t.update(name="Empenhado" if t.name == "empenhado" else "Pago"))
    fig_mensal.update_traces(hovertemplate="%{x}<br>R$ %{y:,.0f}<extra></extra>")
    fig_mensal.update_layout(
        yaxis=dict(tickprefix="R$ ", tickformat=",.0f"),
        xaxis=dict(tickangle=0),
    )
    st.plotly_chart(fig_mensal, use_container_width=True)
else:
    st.info("Sem dados mensais para este ano.")

st.divider()

# ── Natureza do Repasse ──────────────────────────────────────────────────────
st.header("⑥ Natureza do Repasse")
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

st.divider()
st.caption(f"Fonte: [Portal de Transparência]({glossary.PORTAL_URL})")
