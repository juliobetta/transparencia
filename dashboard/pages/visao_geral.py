import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from shared import (
    ANO_ATUAL,
    SPARK_CFG,
    fmt_compact,
    fmt_percent,
    get_conn,
    get_data_extracao,
    pct_delta,
    render_aviso_ano_parcial,
    render_metodologia_receita,
    render_sidebar,
    sparkline,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import (
    adesao_de_ata,
    anomalias_contratuais,
    execucao_orcamentaria,
    folha_vs_servicos,
    fontes_receita,
    licitacao_gaps,
    posicao_fiscal,
    tendencias_anuais,
)

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _orcamento(conn, year, _extracted_at):
    return execucao_orcamentaria.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _licitacoes_gaps(conn, year, _extracted_at):
    return licitacao_gaps.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _contagens_licitacoes(conn, years, _extracted_at):
    return licitacao_gaps.counts_by_year(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _receita(conn, years, _extracted_at):
    return fontes_receita.run(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _folha(conn, years, _extracted_at):
    return folha_vs_servicos.run(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _yoy(conn, years, _extracted_at):
    return tendencias_anuais.run(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_counts(conn, years, _extracted_at):
    return adesao_de_ata.formal_counts_by_year(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_externa_counts(conn, years, _extracted_at):
    return adesao_de_ata.external_counts_by_year(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _contagens_fracionamento(conn, years, _extracted_at):
    return anomalias_contratuais.contagens_fracionamento_por_ano(conn, years)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _fornecedores_pendentes(conn, year, _extracted_at):
    return posicao_fiscal.get_fornecedores_pendentes(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _tendencia_pendentes(conn, years, _extracted_at):
    return posicao_fiscal.get_tendencia_fornecedores_pendentes(conn, years)


conn = get_conn()
year = render_sidebar()
_extracted_at = get_data_extracao(conn)

st.title("Transparência Porciúncula / RJ")
st.caption(f"Dados extraídos do [Portal de Transparência]({glossary.PORTAL_URL}) do município.")
st.header("Visão Geral")

_all_years = list(range(2022, year + 1))
with st.spinner("Carregando..."):
    orcamento = _orcamento(conn, year, _extracted_at)
    licitacoes = _licitacoes_gaps(conn, year, _extracted_at)
    receita = _receita(conn, _all_years, _extracted_at)
    folha = _folha(conn, [year], _extracted_at)
    yoy = _yoy(conn, _all_years, _extracted_at)
    _adesao_map = _adesao_counts(conn, _all_years, _extracted_at)
    _adesao_ext_map = _adesao_externa_counts(conn, _all_years, _extracted_at)
    _mapa_fracionamento = _contagens_fracionamento(conn, _all_years, _extracted_at)
    df_pendentes = _fornecedores_pendentes(conn, year, _extracted_at)
    tendencia_pendentes = _tendencia_pendentes(conn, tuple(_all_years), _extracted_at)

anos = yoy["ano"].tolist()
_mapa_contagens = _contagens_licitacoes(conn, anos, _extracted_at)
_contagens_contratos = [_mapa_contagens[y] for y in anos]

c1, c2, c3, c4 = st.columns(4)

with c1:
    total_gasto = float(yoy.iloc[-1]["total_gasto"]) if not yoy.empty else 0.0
    delta_gasto = yoy.iloc[-1]["total_gasto_pct_change"] if len(yoy) > 1 else None
    st.metric(
        "Total Pago",
        fmt_compact(total_gasto),
        delta=f"{delta_gasto:+.1f}%"
        if year != ANO_ATUAL and delta_gasto is not None and not pd.isna(delta_gasto)
        else None,
        delta_color="off",
        help="Valor total liquidado e pago.",
    )
    st.plotly_chart(
        sparkline(anos, yoy["total_gasto"].tolist()),
        use_container_width=True,
        config=SPARK_CFG,
        key="spark_total_gasto",
    )

with c2:
    if not receita.empty:
        row = receita[receita["ano"] == year].iloc[0] if year in receita["ano"].values else receita.iloc[-1]
        label = "Receita Arrecadada" if year == ANO_ATUAL else "Receita Prevista"
        rev_val = row["total_arrecadado"] if year == ANO_ATUAL else row["total_previsto"]
        _rev_totals = receita["total"].tolist()
        delta_rec = (
            float(receita.iloc[-1]["total_pct_change"])
            if len(receita) > 1 and pd.notna(receita.iloc[-1]["total_pct_change"])
            else None
        )
        help_text = "Total efetivamente arrecadado." if year == ANO_ATUAL else "Previsão orçamentária do ano."
        st.metric(
            label,
            fmt_compact(float(rev_val)),
            delta=f"{delta_rec:+.1f}%"
            if year != ANO_ATUAL and delta_rec is not None and not pd.isna(delta_rec)
            else None,
            help=help_text,
        )
        st.plotly_chart(
            sparkline(anos, receita["total"].tolist(), "#4CAF50"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_receita",
        )

with c3:
    if not folha.empty:
        delta_folha = yoy.iloc[-1]["total_folha_pct_change"] if len(yoy) > 1 else None
        st.metric(
            "Folha / Total Pago",
            fmt_percent(folha.iloc[0]["percentual_folha"]),
            delta=f"{delta_folha:+.1f}%"
            if year != ANO_ATUAL and delta_folha is not None and not pd.isna(delta_folha)
            else None,
            delta_color="inverse" if year != ANO_ATUAL else "off",
        )
        st.plotly_chart(
            sparkline(anos, yoy["total_folha"].tolist(), "#FF9800"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_folha",
        )

with c4:
    restos = float(yoy.iloc[-1]["restos_a_pagar"]) if not yoy.empty else 0.0
    delta_restos = yoy.iloc[-1]["restos_a_pagar_pct_change"] if len(yoy) > 1 else None
    st.metric(
        "Restos Pagos",
        fmt_compact(restos),
        delta=f"{delta_restos:+.1f}%"
        if year != ANO_ATUAL and delta_restos is not None and not pd.isna(delta_restos)
        else None,
        delta_color="off",
        help="Restos a pagar efetivamente pagos no ano.",
    )
    st.plotly_chart(
        sparkline(anos, yoy["restos_a_pagar"].tolist(), "#9C27B0"),
        use_container_width=True,
        config=SPARK_CFG,
        key="spark_restos",
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
        delta=f"{_delta_contratos:+.1f}%" if _delta_contratos is not None else None,
        delta_color="inverse",
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

st.subheader("Tendências Históricas")
col_tendencia, col_pressao = st.columns([6, 4])

with col_tendencia:
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
    _receita_notna = yoy["total_receita"].dropna()
    if len(_receita_notna) >= 2:
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
    elif len(_receita_notna) == 1:
        _receita_val = float(_receita_notna.iloc[0])
        _receita_ano = int(yoy.loc[_receita_notna.index[0], "ano"])
        fig_trend.add_hline(
            y=_receita_val,
            line_dash="dash",
            line_color="#4CAF50",
            line_width=1.5,
            annotation_text=f"Receita {_receita_ano} (parcial)",
            annotation_position="top left",
            annotation_font=dict(color="#4CAF50", size=11),
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
        "Total pago crescendo acima da receita é sinal de desequilíbrio fiscal. Folha persistente acima de 60% do total pago indica rigidez orçamentária — pouco sobra para investimentos."
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
col_donut, col_bar = st.columns([4, 6])

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
                textinfo="percent+label",
                hovertemplate="%{label}<br>R$ %{value:,.0f}<br>%{percent}<extra></extra>",
            )
        )
        fig_donut.update_layout(
            title=titulo_donut,
            showlegend=False,
            margin=dict(l=0, r=0, t=40, b=0),
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

with col_bar:
    _cores_alerta = {
        "normal": "#2196F3",
        "baixa": "#FF9800",
        "excesso": "#F44336",
        "N/D": "#9E9E9E",
    }
    top10 = execucao_orcamentaria.top_orgaos_por_dotacao(orcamento)
    top10["descricao_short"] = top10["descricao"].str[:30]
    top10["bar_color"] = top10["alerta"].map(_cores_alerta).fillna("#9E9E9E")

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
                "total_gasto_pct_change": "Δ% Total Pago",
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
            "Δ% Total Pago": st.column_config.NumberColumn(format="%.2f%%"),
            "Δ% Folha": st.column_config.NumberColumn(format="%.2f%%"),
            "Δ% Receita": st.column_config.NumberColumn(format="%.2f%%"),
            "Δ% Restos": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

st.info(
    f":material/link: Para informações detalhadas, acesse o portal oficial: [{glossary.PORTAL_URL}]({glossary.PORTAL_URL})"
)
