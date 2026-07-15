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
    folha_vs_servicos,
    fontes_receita,
    licitacao_gaps,
    posicao_fiscal,
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


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _folha(conn, years, empresa_ids, _extracted_at):
    return folha_vs_servicos.run(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _cargos_confianca(conn, years, _extracted_at):
    return analise_despesas.get_perfil_cargos_confianca(conn, list(years))


conn = get_conn()
year, empresa_ids = render_sidebar()
_extracted_at = get_data_extracao(conn)

st.title("Transparência Porciúncula / RJ")
st.caption(f"Dados extraídos do [Portal de Transparência]({glossary.PORTAL_URL}) do município.")
st.header("Visão Geral")
render_breadcrumb(year, empresa_ids)

_all_years = list(range(ANO_INICIAL, year + 1))
anos = _all_years

with st.spinner("Carregando..."):
    orcamento = _orcamento(conn, year, empresa_ids, _extracted_at)
    licitacoes = _licitacoes_gaps(conn, year, empresa_ids, _extracted_at)
    receita = _receita(conn, _all_years, empresa_ids, _extracted_at)
    df_composicao = _composicao(conn, year, empresa_ids, _extracted_at)
    _adesao_map = _adesao_counts(conn, _all_years, empresa_ids, _extracted_at)
    _adesao_ext_map = _adesao_externa_counts(conn, _all_years, empresa_ids, _extracted_at)
    _mapa_fracionamento = _contagens_fracionamento(conn, _all_years, empresa_ids, _extracted_at)
    df_pendentes = _fornecedores_pendentes(conn, year, empresa_ids, _extracted_at)
    tendencia_pendentes = _tendencia_pendentes(conn, tuple(_all_years), empresa_ids, _extracted_at)
    df_folha_resumo = _folha(conn, _all_years, empresa_ids, _extracted_at)
    df_cargos = _cargos_confianca(conn, tuple(_all_years), _extracted_at)

_mapa_contagens = _contagens_licitacoes(conn, anos, empresa_ids, _extracted_at)
_contagens_contratos = [_mapa_contagens[y] for y in anos]

# ── RECEITAS ──────────────────────────────────────────────────────────────────
st.subheader("Receitas")
render_metodologia_receita()

_receita_row = (
    receita[receita["ano"] == year].iloc[0]
    if (not receita.empty and year in receita["ano"].values)
    else (receita.iloc[-1] if not receita.empty else None)
)
_tem_arrecadado = _receita_row is not None and float(_receita_row["total_arrecadado"]) > 0

r1, r2, r3, _ = st.columns(4)
if _receita_row is not None:
    _prev_serie = receita["total_previsto"].tolist()
    _total_serie = receita["total"].tolist()
    _anos_rec = receita["ano"].tolist()
    with r1:
        st.metric(
            "Previsão Orçamentária",
            fmt_compact(float(_receita_row["total_previsto"])),
            delta=pct_delta(_prev_serie),
            delta_color="off",
            help="Valor total de receitas que a prefeitura planejou arrecadar no ano, conforme aprovado na Lei Orçamentária Anual (LOA).",
        )
        st.plotly_chart(
            sparkline(_anos_rec, _prev_serie, "#2196F3"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_rec_prev",
        )
    with r2:
        if _tem_arrecadado:
            st.metric(
                "Total Arrecadado Real",
                fmt_compact(float(_receita_row["total_arrecadado"])),
                delta="—" if year == ANO_ATUAL else pct_delta(_total_serie),
                delta_color="off",
                help="Valor efetivamente recebido pela prefeitura — impostos, FPM, FUNDEB, ICMS e demais transferências.",
            )
            st.plotly_chart(
                sparkline(_anos_rec, _total_serie, "#4CAF50"),
                use_container_width=True,
                config=SPARK_CFG,
                key="spark_rec_total",
            )
        else:
            st.metric("Total Arrecadado Real", "N/D")
    with r3:
        if _tem_arrecadado:
            _pct_rec = float(_receita_row["pct_arrecadado"])
            st.metric(
                "% Realizado",
                f"{_pct_rec:.1%}",
                delta_color="off",
                help="Quanto da previsão orçamentária já foi efetivamente arrecadado.",
            )
            st.progress(min(_pct_rec, 1.0))
    if year == ANO_ATUAL:
        render_aviso_ano_parcial(year, _extracted_at)
else:
    st.info("Dados de receita não disponíveis.")

if not receita.empty:
    row_rec = receita[receita["ano"] == year].iloc[0] if year in receita["ano"].values else receita.iloc[-1]
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
                float(row_rec["receita_propria"]),
                float(row_rec["transferencias_uniao"]),
                float(row_rec["transferencias_estado"]),
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
    st.caption(
        "Alta dependência de transferências federais e estaduais fragiliza o município diante de mudanças na política fiscal nacional. "
        "Receita própria elevada indica maior autonomia."
    )

st.page_link("pages/receitas.py", label="Ver detalhes em Fontes de Receita →", icon=":material/arrow_forward:")

# ── EXECUÇÃO ORÇAMENTÁRIA ─────────────────────────────────────────────────────
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
        "Total Empenhado",
        fmt_compact(_emp),
        delta=f"{_pct_emp:.1%} da dotação",
        delta_color=_exec_delta_color,
        help=glossary.tooltip("Empenho"),
    )
    st.progress(min(_pct_emp, 1.0))

with h3:
    st.metric(
        "Total Liquidado",
        fmt_compact(_liq),
        delta=f"{_pct_liq:.1%} da dotação",
        delta_color="off",
        help=glossary.tooltip("Liquidação"),
    )
    st.progress(min(_pct_liq, 1.0))

with h4:
    st.metric(
        "Total Pago",
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
st.page_link("pages/orcamento.py", label="Ver detalhes em Execução Orçamentária →", icon=":material/arrow_forward:")

# ── DESPESAS DETALHADAS ───────────────────────────────────────────────────────
st.subheader("Despesas Detalhadas")

if not df_pendentes.empty:
    total_pendente = df_pendentes["pendente"].sum()
    num_fornecedores = len(df_pendentes)
    ano_mais_antigo = int(df_pendentes["aguardando_desde"].min())

    _valores_tendencia = tendencia_pendentes["total_pendente"].tolist() if not tendencia_pendentes.empty else []
    _contagem_tendencia = tendencia_pendentes["num_fornecedores"].tolist() if not tendencia_pendentes.empty else []
    _anos_tendencia = tendencia_pendentes["ano"].tolist() if not tendencia_pendentes.empty else []

    rp1, rp2, rp3, _ = st.columns(4)

    with rp1:
        st.metric(
            "Total Pendente (Restos a Pagar)",
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
else:
    st.info("Nenhum empenho com Restos a Pagar para o período selecionado.")

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
        "Composição do total pago por natureza de despesa — revela se o orçamento é rígido (dominado por pessoal) "
        "ou tem espaço para serviços e investimentos."
    )

st.page_link("pages/despesas.py", label="Ver detalhes em Despesas →", icon=":material/arrow_forward:")

# ── LICITAÇÕES E CONTRATOS ────────────────────────────────────────────────────
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

st.page_link("pages/licitacoes.py", label="Ver detalhes em Licitações e Contratos →", icon=":material/arrow_forward:")

# ── PESSOAL ───────────────────────────────────────────────────────────────────
st.subheader("Pessoal")

p1, p2, p3, _ = st.columns(4)

if not df_folha_resumo.empty:
    _folha_ano = df_folha_resumo[df_folha_resumo["ano"] == year]
    _row_folha = _folha_ano.iloc[0] if not _folha_ano.empty else df_folha_resumo.iloc[-1]
    _total_folha = float(_row_folha["total_folha"])
    _pct_folha = float(_row_folha["percentual_folha"])
    _pct_serie = df_folha_resumo["percentual_folha"].tolist()
    _folha_serie = df_folha_resumo["total_folha"].tolist()
    _anos_folha = df_folha_resumo["ano"].tolist()

    with p1:
        st.metric(
            "Total Pago em Folha",
            fmt_compact(_total_folha),
            delta=pct_delta(_folha_serie) if year != ANO_ATUAL else "—",
            delta_color="off",
            help="Total de proventos brutos pagos a servidores no ano.",
        )
        st.plotly_chart(
            sparkline(_anos_folha, _folha_serie, "#607D8B"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_pes_folha",
        )

    with p2:
        st.metric(
            "Folha / Receita Arrecadada",
            f"{_pct_folha:.1f}%",
            delta=pct_delta(_pct_serie) if year != ANO_ATUAL else "—",
            delta_color="inverse" if year != ANO_ATUAL else "off",
            help="Percentual da receita arrecadada comprometido com folha de pessoal. A LRF limita a 54% da RCL para o Poder Executivo.",
        )
        st.plotly_chart(
            sparkline(_anos_folha, _pct_serie, "#FF9800"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_pes_pct",
        )
else:
    st.info("Dados de folha de pagamento não disponíveis.")

if not df_cargos.empty:
    _series_pct_efetivos = []
    _anos_cargos_serie = []
    for _y in sorted(df_cargos["ano"].unique()):
        if _y > year:
            continue
        _qty = df_cargos[df_cargos["ano"] == _y].set_index("tipo_vinculo_detalhado")["quantidade"].to_dict()
        _efetivos = _qty.get("Servidor Efetivo com Função de Confiança (DAI/FG)", 0) + _qty.get(
            "Servidor Efetivo com Cargo Comissionado (DAS/CC)", 0
        )
        _total_conf = _efetivos + _qty.get("Comissionado Externo (DAS/CC - Sem Vínculo)", 0)
        _series_pct_efetivos.append((_efetivos / _total_conf * 100) if _total_conf > 0 else 0.0)
        _anos_cargos_serie.append(_y)

    if _series_pct_efetivos:
        with p3:
            st.metric(
                "Efetivos no Comando das Chefias",
                f"{_series_pct_efetivos[-1]:.1f}%",
                delta=pct_delta(_series_pct_efetivos),
                help="Percentual de cargos de liderança (DAS/DAI) ocupados por servidores concursados. Quanto maior, mais técnica e profissionalizada é a gestão.",
            )
            if len(_series_pct_efetivos) > 1:
                st.plotly_chart(
                    sparkline(_anos_cargos_serie, _series_pct_efetivos, "#2196F3"),
                    use_container_width=True,
                    config=SPARK_CFG,
                    key="spark_pes_cargos",
                )

st.page_link("pages/pessoal.py", label="Ver detalhes em Pessoal →", icon=":material/arrow_forward:")

st.info(
    f":material/link: Para informações detalhadas, acesse o portal oficial: [{glossary.PORTAL_URL}]({glossary.PORTAL_URL})"
)
