import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Any, Literal

import plotly.graph_objects as go
import streamlit as st
from shared import (
    ANO_ATUAL,
    ANO_INICIAL,
    SPARK_CFG,
    fmt_compact,
    get_conn,
    get_data_extracao,
    pct_delta,
    render_aviso_ano_parcial,
    render_breadcrumb,
    render_metodologia_receita,
    render_sidebar,
    sparkline,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import (
    adesao_de_ata,
    analise_despesas,
    anomalias_contratuais,
    execucao_orcamentaria,
    fontes_receita,
    licitacao_gaps,
    posicao_fiscal,
    tendencias_anuais,
)

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _orcamento(conn, year, empresa_ids, _extracted_at):
    return execucao_orcamentaria.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _licitacoes_gaps(conn, year, empresa_ids, _extracted_at):
    return licitacao_gaps.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _contagens_licitacoes(conn, years, empresa_ids, _extracted_at):
    return licitacao_gaps.counts_by_year(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _receita(conn, years, empresa_ids, _extracted_at):
    return fontes_receita.run(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _yoy(conn, years, empresa_ids, _extracted_at):
    return tendencias_anuais.run(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_counts(conn, years, empresa_ids, _extracted_at):
    return adesao_de_ata.formal_counts_by_year(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_externa_counts(conn, years, empresa_ids, _extracted_at):
    return adesao_de_ata.external_counts_by_year(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _contagens_fracionamento(conn, years, empresa_ids, _extracted_at):
    return anomalias_contratuais.contagens_fracionamento_por_ano(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _fornecedores_pendentes(conn, year, empresa_ids, _extracted_at):
    return posicao_fiscal.get_fornecedores_pendentes(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _tendencia_pendentes(conn, years, empresa_ids, _extracted_at):
    return posicao_fiscal.get_tendencia_fornecedores_pendentes(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _composicao(conn, year, empresa_ids, _extracted_at):
    return analise_despesas.get_composicao_despesa(conn, year, empresa_ids=empresa_ids)


conn = get_conn()
year, empresa_ids = render_sidebar()
_extracted_at = get_data_extracao(conn)

st.title("Transparência Porciúncula / RJ")
st.caption(f"Dados extraídos do [Portal de Transparência]({glossary.PORTAL_URL}) do município.")
st.header("Visão Geral")
render_breadcrumb(year, empresa_ids)

_all_years = list(range(ANO_INICIAL, year + 1))
with st.spinner("Carregando..."):
    orcamento = _orcamento(conn, year, empresa_ids, _extracted_at)
    licitacoes = _licitacoes_gaps(conn, year, empresa_ids, _extracted_at)
    receita = _receita(conn, _all_years, empresa_ids, _extracted_at)
    yoy = _yoy(conn, _all_years, empresa_ids, _extracted_at)
    df_composicao = _composicao(conn, year, empresa_ids, _extracted_at)
    _adesao_map = _adesao_counts(conn, _all_years, empresa_ids, _extracted_at)
    _adesao_ext_map = _adesao_externa_counts(conn, _all_years, empresa_ids, _extracted_at)
    _mapa_fracionamento = _contagens_fracionamento(conn, _all_years, empresa_ids, _extracted_at)
    df_pendentes = _fornecedores_pendentes(conn, year, empresa_ids, _extracted_at)
    tendencia_pendentes = _tendencia_pendentes(conn, tuple(_all_years), empresa_ids, _extracted_at)

anos = yoy["ano"].tolist()
_mapa_contagens = _contagens_licitacoes(conn, anos, empresa_ids, _extracted_at)
_contagens_contratos = [_mapa_contagens[y] for y in anos]

st.subheader("Execução Orçamentária")
_dot = float(orcamento["dotacao_atualizada"].sum()) if not orcamento.empty else 0.0
_emp = float(orcamento["empenhado"].sum()) if not orcamento.empty else 0.0
_liq = float(orcamento["liquidado"].sum()) if not orcamento.empty else 0.0
_pago = float(orcamento["pago"].sum()) if not orcamento.empty else 0.0

_pct_emp = _emp / _dot if _dot > 0 else 0.0
_pct_liq = _liq / _dot if _dot > 0 else 0.0
_pct_pago = _pago / _dot if _dot > 0 else 0.0

_exec_delta_color: Literal["normal", "off", "inverse"] = (
    "normal" if _pct_emp >= 0.7 else ("off" if _pct_emp >= 0.3 else "inverse")
)

h1, h2, h3, h4 = st.columns(4)

with h1:
    st.metric(
        "Dotação Atualizada",
        fmt_compact(_dot),
        delta="—",
        delta_color="off",
        help=glossary.tooltip("Dotação Atualizada"),
    )
    st.progress(1.0)
    st.caption("100% — orçamento autorizado")

with h2:
    st.metric(
        "Empenhado",
        fmt_compact(_emp),
        delta=f"{_pct_emp:.1%} da dotação",
        delta_color=_exec_delta_color,
        help=glossary.tooltip("Empenho"),
    )
    st.progress(min(_pct_emp, 1.0))
    st.caption("Abaixo de 70% ao fim do ano indica sub-execução." if year == ANO_ATUAL else "")

with h3:
    st.metric(
        "Liquidado",
        fmt_compact(_liq),
        delta=f"{_pct_liq:.1%} da dotação",
        delta_color="off",
        help=glossary.tooltip("Liquidação"),
    )
    st.progress(min(_pct_liq, 1.0))

with h4:
    st.metric(
        "Pago",
        fmt_compact(_pago),
        delta=f"{_pct_pago:.1%} da dotação",
        delta_color="off",
        help=glossary.tooltip("Pagamento"),
    )
    st.progress(min(_pct_pago, 1.0))

st.info(
    "A cadeia **Dotação → Empenhado → Liquidado → Pago** mostra o ciclo completo da despesa pública. "
    "Cada etapa é um estágio legal: reservar, confirmar entrega e pagar.",
    icon=":material/info:",
)

if not df_pendentes.empty:
    total_pendente = df_pendentes["pendente"].sum()
    num_fornecedores = len(df_pendentes)
    ano_mais_antigo = int(df_pendentes["aguardando_desde"].min())

    _valores_tendencia = tendencia_pendentes["total_pendente"].tolist() if not tendencia_pendentes.empty else []
    _contagem_tendencia = tendencia_pendentes["num_fornecedores"].tolist() if not tendencia_pendentes.empty else []
    _anos_tendencia = tendencia_pendentes["ano"].tolist() if not tendencia_pendentes.empty else []

    st.subheader("Restos a Pagar — Obrigações Pendentes")
    rp1, rp2, rp3, _ = st.columns(4)

    with rp1:
        st.metric(
            "Total a Pagar a Fornecedores",
            fmt_compact(total_pendente),
            delta=pct_delta(_valores_tendencia),
            delta_color="inverse",
            help="Soma de todos os empenhos ainda não quitados na tabela de Restos a Pagar.",
        )
        if _valores_tendencia:
            st.plotly_chart(
                sparkline(_anos_tendencia, _valores_tendencia, "#E91E63"),
                use_container_width=True,
                config=SPARK_CFG,
                key="spark_rp_total",
            )

    with rp2:
        st.metric(
            "Fornecedores aguardando",
            num_fornecedores,
            delta=pct_delta(_contagem_tendencia),
            delta_color="inverse",
            help="Número de fornecedores com pelo menos um empenho não totalmente pago.",
        )
        if _contagem_tendencia:
            st.plotly_chart(
                sparkline(_anos_tendencia, _contagem_tendencia, "#FF5722"),
                use_container_width=True,
                config=SPARK_CFG,
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

st.subheader("Licitações e Contratos")
_lista_licitacoes = [_mapa_contagens[y] for y in anos]
_adesao_counts_list = [_adesao_map[y] for y in anos]
_adesao_ext_counts_list = [_adesao_ext_map[y] for y in anos]
_contagens_fracionamento_list = [_mapa_fracionamento[y] for y in anos]

lc1, lc2, lc3, lc4 = st.columns(4)

with lc1:
    contratos_sem_licitacao = int(licitacoes["acima_limite"].sum())
    _delta_contratos = (
        (_contagens_contratos[-1] - _contagens_contratos[-2]) / _contagens_contratos[-2] * 100
        if len(_contagens_contratos) > 1 and _contagens_contratos[-2] != 0
        else None
    )
    st.metric(
        "Acima do limite s/ licitação",
        contratos_sem_licitacao,
        delta=f"{_delta_contratos:+.1f}%" if _delta_contratos is not None else "—",
        delta_color="inverse" if _delta_contratos is not None else "off",
        help="Contratos sem licitação acima de R$ 62.725,59 (bens e serviços). [Lei 14.133/21, Art. 75, I](https://licitacoesecontratos.tcu.gov.br/5-10-2-1-dispensa-em-razao-do-valor-incisos-i-e-ii-2/)",
    )
    st.plotly_chart(
        sparkline(anos, _lista_licitacoes, "#E91E63"),
        use_container_width=True,
        config=SPARK_CFG,
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
        sparkline(anos, _adesao_counts_list, "#FF9800"),
        use_container_width=True,
        config=SPARK_CFG,
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
        sparkline(anos, _adesao_ext_counts_list, "#9C27B0"),
        use_container_width=True,
        config=SPARK_CFG,
        key="spark_lc_ext",
    )

with lc4:
    _delta_fracionamento = (
        (_contagens_fracionamento_list[-1] - _contagens_fracionamento_list[-2])
        / _contagens_fracionamento_list[-2]
        * 100
        if len(_contagens_fracionamento_list) > 1 and _contagens_fracionamento_list[-2] != 0
        else None
    )
    st.metric(
        "Possível fracionamento",
        _mapa_fracionamento[year],
        delta=f"{_delta_fracionamento:+.1f}%" if _delta_fracionamento is not None else None,
        delta_color="inverse",
        help="Contratos do mesmo fornecedor com valores próximos ao limite de dispensa (R$ 62.725,59), sugerindo possível fracionamento.",
    )
    st.plotly_chart(
        sparkline(anos, _contagens_fracionamento_list, "#F44336"),
        use_container_width=True,
        config=SPARK_CFG,
        key="spark_lc_split",
    )


st.subheader("Tendências Históricas")
col_tendencia, col_pressao = st.columns([6, 4])

with col_tendencia:
    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Bar(
            x=anos,
            y=yoy["total_empenhado"].tolist(),
            name="Empenhado",
            marker_color="rgba(33,150,243,0.35)",
        )
    )
    fig_trend.add_trace(
        go.Bar(
            x=anos,
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

render_metodologia_receita()

st.subheader(f"Composição e Execução ({year})")
col_donut, col_funcional = st.columns(2)

with col_donut:
    if not receita.empty:
        row = receita[receita["ano"] == year].iloc[0] if year in receita["ano"].values else receita.iloc[-1]
        eh_parcial = year == ANO_ATUAL
        titulo_donut = (
            f"Fontes de Receita ({year} — Arrecadado Parcial)"
            if eh_parcial
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
                textinfo="percent",
                textposition="inside",
                automargin=True,
                hovertemplate="%{label}<br>R$ %{value:,.0f}<br>%{percent}<extra></extra>",
            )
        )
        fig_donut.update_layout(
            title=titulo_donut,
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
            margin=dict(l=0, r=0, t=40, b=80),
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        if eh_parcial:
            _rows_anteriores = receita[receita["ano"] == year - 1]
            _propria_cur = fmt_compact(float(row["receita_propria_previsto"]))
            _propria_prev = (
                fmt_compact(float(_rows_anteriores.iloc[0]["receita_propria_previsto"]))
                if not _rows_anteriores.empty
                else "N/D"
            )
            _pct_cur = float(row["pct_propria"])
            _pct_prev = float(_rows_anteriores.iloc[0]["pct_propria"]) if not _rows_anteriores.empty else 0
            render_aviso_ano_parcial(
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

with col_funcional:
    if not df_composicao.empty:
        fig_comp = go.Figure(
            go.Pie(
                labels=df_composicao["categoria"].tolist(),
                values=df_composicao["pago"].tolist(),
                hole=0.5,
                textinfo="percent",
                textposition="inside",
                automargin=True,
                hovertemplate="%{label}<br>R$ %{value:,.0f}<br>%{percent}<extra></extra>",
            )
        )
        fig_comp.update_layout(
            title=f"Como o dinheiro é gasto ({year})",
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
            margin=dict(l=0, r=0, t=40, b=80),
        )
        st.plotly_chart(fig_comp, use_container_width=True)
        st.caption(
            "Composição do total pago por natureza de despesa — revela se o orçamento é rígido (dominado por pessoal) ou tem espaço para serviços e investimentos."
        )
    else:
        st.info("Dados de composição de despesa não disponíveis.")

with st.expander(":material/bar_chart: Dados detalhados por ano"):
    st.dataframe(
        yoy.rename(
            columns={
                "ano": "Ano",
                "total_gasto": "Total Pago",
                "total_empenhado": "Total Empenhado",
                "total_folha": "Total Folha",
                "total_receita": "Total Receita",
                "restos_a_pagar": "Restos Pago",
                "total_gasto_pct_change": "Δ% Total Pago",
                "total_empenhado_pct_change": "Δ% Empenhado",
                "total_folha_pct_change": "Δ% Folha",
                "total_receita_pct_change": "Δ% Receita",
                "restos_a_pagar_pct_change": "Δ% Restos",
            }
        ),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Total Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Total Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Total Folha": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Total Receita": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Restos Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Δ% Total Pago": st.column_config.NumberColumn(format="%.2f%%"),
            "Δ% Empenhado": st.column_config.NumberColumn(format="%.2f%%"),
            "Δ% Folha": st.column_config.NumberColumn(format="%.2f%%"),
            "Δ% Receita": st.column_config.NumberColumn(format="%.2f%%"),
            "Δ% Restos": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

st.info(
    f":material/link: Para informações detalhadas, acesse o portal oficial: [{glossary.PORTAL_URL}]({glossary.PORTAL_URL})"
)
