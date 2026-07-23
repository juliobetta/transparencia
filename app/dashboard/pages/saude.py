import sys
from pathlib import Path
from typing import Any

import pandas as pd

import constants

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import plotly.graph_objects as go
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

from app import glossary
from app.analytics import adesao_de_ata, fontes_receita, historia_saude, licitacao_gaps

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _saude(conn, year, _extracted_at):
    return historia_saude.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_externa(conn, year, _extracted_at):
    return adesao_de_ata.run_external(conn, year, empresa_ids=["2"])


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _receita_saude(conn, years, _extracted_at):
    return fontes_receita.run(conn, years, empresa_ids=["2"])


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_counts_saude(conn, years, _extracted_at):
    return adesao_de_ata.formal_counts_by_year(conn, years, empresa_ids=["2"])


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_ext_counts_saude(conn, years, _extracted_at):
    return adesao_de_ata.external_counts_by_year(conn, years, empresa_ids=["2"])


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _licitacao_counts_saude(conn, years, _extracted_at):
    return licitacao_gaps.counts_by_year(conn, years, empresa_ids=["2"])


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _tendencias_saude(conn, _extracted_at):
    return historia_saude.run_tendencias(conn)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _pdf(conn, year, _extracted_at):
    from app.report.saude_pdf import generate as generate_pdf

    return generate_pdf(conn, year)


conn = get_conn()
year, _ = render_sidebar()
_extracted_at = get_data_extracao(conn)

col_titulo, col_botao = st.columns([8, 2])
with col_titulo:
    st.title(f"Fundo Municipal de Saúde - {year}")
    st.caption(f"Dados do Fundo Municipal de Saúde extraídos do [Portal de Transparência]({constants.PORTAL_URL}).")
with col_botao:
    st.write("")
    st.write("")
    pdf_bytes = _pdf(conn, year, _extracted_at)
    st.download_button(
        label="⬇ Baixar PDF",
        data=pdf_bytes,
        file_name=f"saude-{year}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

if year == ANO_ATUAL:
    render_aviso_ano_parcial(year, _extracted_at)

_all_years = list(range(2020, year + 1))

dados = _saude(conn, year, _extracted_at)
adesao_externa = _adesao_externa(conn, year, _extracted_at)
receita_saude = _receita_saude(conn, _all_years, _extracted_at)
_adesao_map = _adesao_counts_saude(conn, _all_years, _extracted_at)
_adesao_ext_map = _adesao_ext_counts_saude(conn, _all_years, _extracted_at)
_licit_map = _licitacao_counts_saude(conn, _all_years, _extracted_at)

_adesao_serie = [_adesao_map[y] for y in _all_years]
_adesao_ext_serie = [_adesao_ext_map[y] for y in _all_years]
_licit_serie = [_licit_map[y] for y in _all_years]
tendencias = _tendencias_saude(conn, _extracted_at)


def _trend_series(df: pd.DataFrame, col: str) -> list:
    if df.empty or col not in df.columns:
        return []
    return list(df.set_index("ano")[col].reindex(_all_years, fill_value=0))


_emendas_serie = _trend_series(tendencias["emendas_por_ano"], "total")
_transferencias_serie = _trend_series(tendencias["transferencias_por_ano"], "total")
_adesao_valor_serie = _trend_series(tendencias["adesao_por_ano"], "valor")
_adesao_contratos_serie = _trend_series(tendencias["adesao_por_ano"], "contratos_linked")
_hhi_serie = _trend_series(tendencias["hhi_por_ano"], "hhi")
_pharma_jud_serie = _trend_series(tendencias["pharma_judicial_por_ano"], "total")

# Criar coluna MM/AAAA para exibição
for key, val in dados.items():
    if isinstance(val, pd.DataFrame) and "mes" in val.columns:
        if "ano" in val.columns:
            val["periodo"] = val["mes"].astype(str).str.zfill(2) + "/" + val["ano"].astype(str)
        else:
            val["periodo"] = val["mes"].astype(str).str.zfill(2) + "/" + str(year)

# ── KPIs resumo ─────────────────────────────────────────────────────────────
orcamento = dados["orcamento"]
tendencia_orcamento = dados["tendencia_orcamento"]
tendencia_ate_ano = tendencia_orcamento[tendencia_orcamento["ano"] <= year]
tendencia_farma = dados["pharma_empenhos"]["trend"]
tendencia_farma_ate_ano = tendencia_farma[tendencia_farma["ano"] <= year]

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "Dotação Atualizada",
        fmt_compact(orcamento["dotacao"]),
        delta=pct_delta(tendencia_ate_ano["dotacao"].tolist()),
        delta_color="off",
        help=glossary.tooltip("Dotação Atualizada"),
    )
    if len(tendencia_ate_ano) >= 2:
        st.plotly_chart(
            sparkline(tendencia_ate_ano["ano"].tolist(), tendencia_ate_ano["dotacao"].tolist()),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_dotacao",
        )

with k2:
    st.metric(
        "Total Empenhado",
        fmt_compact(orcamento["empenhado"]),
        delta=pct_delta(tendencia_ate_ano["empenhado"].tolist()) if year != ANO_ATUAL else "—",
        delta_color="off",
        help=glossary.tooltip("Empenho"),
    )
    if len(tendencia_ate_ano) >= 2:
        st.plotly_chart(
            sparkline(tendencia_ate_ano["ano"].tolist(), tendencia_ate_ano["empenhado"].tolist(), "#4CAF50"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_empenhado",
        )

with k3:
    st.metric(
        "Taxa de Execução",
        f"{orcamento['taxa_execucao']:.1%}",
        delta=pct_delta(tendencia_ate_ano["taxa"].tolist()) if year != ANO_ATUAL else "—",
        delta_color="off" if year == ANO_ATUAL else "normal",
    )
    if len(tendencia_ate_ano) >= 2:
        st.plotly_chart(
            sparkline(tendencia_ate_ano["ano"].tolist(), tendencia_ate_ano["taxa"].tolist(), "#FF9800"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_taxa",
        )

with k4:
    st.metric(
        "Medicamentos e Insumos",
        fmt_compact(dados["pharma_empenhos"]["total"]),
        delta=pct_delta(tendencia_farma_ate_ano["empenhado"].tolist()),
        delta_color="off",
        help="Total empenhado em Material de Consumo na Subfunção 10.303 (Suporte Profilático e Terapêutico).",
    )
    if len(tendencia_farma_ate_ano) >= 2:
        st.plotly_chart(
            sparkline(
                tendencia_farma_ate_ano["ano"].tolist(), tendencia_farma_ate_ano["empenhado"].tolist(), "#9C27B0"
            ),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_pharma",
        )

st.divider()

# ── Seção 1: O que entrou ───────────────────────────────────────────────────
st.header("① O que entrou")

if orcamento["alerta_sub_execucao"]:
    st.warning(f"Taxa de execução abaixo de 70% ao final do ano {year}.", icon=":material/warning:")

st.subheader("Emendas Parlamentares")
if dados["emendas_total"] > 0:
    e1, _, _, _ = st.columns(4)
    with e1:
        st.metric(
            "Total de emendas",
            fmt_compact(dados["emendas_total"]),
            delta=pct_delta(_emendas_serie) if len(_emendas_serie) >= 2 else None,
            delta_color="off",
        )
        if len(_emendas_serie) >= 2:
            st.plotly_chart(
                sparkline(_all_years, _emendas_serie, "#2196F3"),
                use_container_width=True,
                config=SPARK_CFG,
                key="spark_emendas",
            )
    if not dados["emendas"].empty and dados["emendas"].notna().any().any():
        st.dataframe(
            dados["emendas"].rename(
                columns={
                    "numero": "Nº",
                    "descricao": "Objeto",
                    "Período": "Período",
                    "valor": "Valor Autorizado",
                    "empenhado": "Empenhado",
                    "autor": "Autor",
                    "Tipo da Emenda": "Tipo da Emenda",
                    "Esfera de Origem": "Esfera de Origem",
                    "ato_normativo": "Ato Normativo",
                    "Destinação": "Destinação",
                }
            ),
            width="stretch",
            column_config={
                "Valor Autorizado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Nº": None,
                "Tipo da Emenda": None,
                "Esfera de Origem": None,
                "Destinação": None,
            },
            hide_index=True,
        )
    with st.expander(":material/info: O que é uma emenda parlamentar?"):
        st.write(glossary.tooltip("Emenda Impositiva"))
else:
    st.info("Sem emendas parlamentares registradas para este ano.")

st.subheader("Repasses da Prefeitura")
total_repasses = dados["transferencias_saude_total"]
rp1, _, _, _ = st.columns(4)
if total_repasses > 0:
    with rp1:
        st.metric(
            "Total de repasses",
            fmt_compact(total_repasses),
            delta=pct_delta(_transferencias_serie) if len(_transferencias_serie) >= 2 else None,
            delta_color="off",
            help="Valores transferidos pela Prefeitura Municipal ao Fundo de Saúde no ano.",
        )
        if len(_transferencias_serie) >= 2:
            st.plotly_chart(
                sparkline(_all_years, _transferencias_serie, "#4CAF50"),
                use_container_width=True,
                config=SPARK_CFG,
                key="spark_repasses",
            )
else:
    rp1.info("Sem repasses registrados para este ano.")

st.subheader("Fontes de Receita do Fundo")
if not receita_saude.empty:
    _anos_rec = receita_saude["ano"].tolist()
    _rec_row = (
        receita_saude[receita_saude["ano"] == year].iloc[0]
        if year in receita_saude["ano"].values
        else receita_saude.iloc[-1]
    )
    r1, r2, r3, _ = st.columns(4)
    with r1:
        st.metric(
            "Receita Própria",
            fmt_compact(float(_rec_row["receita_propria"])),
            delta=pct_delta(receita_saude["receita_propria"].tolist()),
            delta_color="off",
        )
        if len(_anos_rec) >= 2:
            st.plotly_chart(
                sparkline(_anos_rec, receita_saude["receita_propria"].tolist(), "#2196F3"),
                use_container_width=True,
                config=SPARK_CFG,
                key="spark_rec_propria",
            )
    with r2:
        st.metric(
            "Transferências União",
            fmt_compact(float(_rec_row["transferencias_uniao"])),
            delta=pct_delta(receita_saude["transferencias_uniao"].tolist()),
            delta_color="off",
        )
        if len(_anos_rec) >= 2:
            st.plotly_chart(
                sparkline(_anos_rec, receita_saude["transferencias_uniao"].tolist(), "#4CAF50"),
                use_container_width=True,
                config=SPARK_CFG,
                key="spark_rec_uniao",
            )
    with r3:
        st.metric(
            "Transferências Estado",
            fmt_compact(float(_rec_row["transferencias_estado"])),
            delta=pct_delta(receita_saude["transferencias_estado"].tolist()),
            delta_color="off",
        )
        if len(_anos_rec) >= 2:
            st.plotly_chart(
                sparkline(_anos_rec, receita_saude["transferencias_estado"].tolist(), "#FF9800"),
                use_container_width=True,
                config=SPARK_CFG,
                key="spark_rec_estado",
            )

    fig_donut = go.Figure(
        go.Pie(
            labels=["Receita Própria", "Transferências União", "Transferências Estado"],
            values=[
                float(_rec_row["receita_propria"]),
                float(_rec_row["transferencias_uniao"]),
                float(_rec_row["transferencias_estado"]),
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
        title=f"Fontes de Receita do Fundo de Saúde ({year})",
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
        margin=dict(l=0, r=0, t=40, b=80),
    )
    st.plotly_chart(fig_donut, use_container_width=True)
    st.caption(
        "Composição da receita do Fundo Municipal de Saúde — revela dependência de transferências federais "
        "(SUS, PAB, etc.) vs receita própria."
    )

st.page_link("pages/receitas.py", label="Ver detalhes em Fontes de Receita →", icon=":material/arrow_forward:")

# ── Seção 2: O que foi gasto ────────────────────────────────────────────────
st.header("② O que foi empenhado")
st.subheader("Evolução do Empenhado por Ano")
tendencia_execucao = dados["tendencia_execucao"]
if not tendencia_execucao.empty:
    fig = px.bar(
        tendencia_execucao,
        x="ano",
        y="empenhado",
        title="Fundo de Saúde — Empenhado por Ano",
        labels={"ano": "Ano", "empenhado": "Empenhado"},
    )
    fig.update_traces(hovertemplate="Ano: %{x}<br>Empenhado: R$ %{y:,.0f}<extra></extra>")
    fig.update_layout(yaxis=dict(tickprefix="R$ ", tickformat=",.0f"))
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(fig, width="stretch")

    st.dataframe(
        tendencia_execucao.rename(columns={"ano": "Ano", "empenhado": "Empenhado"}),
        width="stretch",
        hide_index=True,
        column_config={
            "Ano": st.column_config.NumberColumn(format="%d"),
            "Empenhado": st.column_config.NumberColumn(format="R$ %,.0f"),
        },
    )

st.page_link("pages/orcamento.py", label="Ver detalhes em Execução Orçamentária →", icon=":material/arrow_forward:")

# ── Seção 3: Como foi contratado ────────────────────────────────────────────
st.header("③ Como foi contratado")

_delta_adesao = (
    (_adesao_serie[-1] - _adesao_serie[-2]) / _adesao_serie[-2] * 100
    if len(_adesao_serie) > 1 and _adesao_serie[-2] != 0
    else None
)

c1, c2, c3, _ = st.columns(4)
with c1:
    st.metric(
        "Adesões de Ata (Carona)",
        dados["adesao_de_ata_count"],
        delta=f"{_delta_adesao:+.1f}%" if _delta_adesao is not None else None,
        delta_color="inverse",
        help=glossary.tooltip("Adesão de Ata (Carona)"),
    )
    if len(_all_years) >= 2:
        st.plotly_chart(
            sparkline(_all_years, _adesao_serie, "#FF9800"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_adesao_count",
        )
with c2:
    _delta_contratos = (
        (_adesao_contratos_serie[-1] - _adesao_contratos_serie[-2]) / _adesao_contratos_serie[-2] * 100
        if len(_adesao_contratos_serie) > 1 and _adesao_contratos_serie[-2] != 0
        else None
    )
    st.metric(
        "Contratos Vinculados",
        dados["adesao_de_ata_contracts_linked"],
        delta=f"{_delta_contratos:+.1f}%" if _delta_contratos is not None else None,
        delta_color="off",
    )
    if len(_adesao_contratos_serie) >= 2:
        st.plotly_chart(
            sparkline(_all_years, _adesao_contratos_serie, "#FF9800"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_adesao_contratos",
        )
with c3:
    st.metric(
        "Valor Contratado (Adesão)",
        fmt_compact(dados["adesao_de_ata_value"]),
        delta=pct_delta(_adesao_valor_serie) if len(_adesao_valor_serie) >= 2 else None,
        delta_color="off",
    )
    if len(_adesao_valor_serie) >= 2:
        st.plotly_chart(
            sparkline(_all_years, _adesao_valor_serie, "#FF5722"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_adesao_valor",
        )

if not dados["adesao_de_ata_list"].empty:
    with st.expander("Ver licitações via Adesão de Ata"):
        _ata_df = dados["adesao_de_ata_list"].copy()
        _ata_df["licitacao_valor"] = pd.to_numeric(
            _ata_df["licitacao_valor"].astype(str).str.replace(",", "."), errors="coerce"
        )
        st.dataframe(
            _ata_df.rename(
                columns={
                    "numero": "Nº Licit.",
                    "objeto": "Objeto",
                    "periodo": "Período",
                    "licitacao_valor": "Valor Est. Licitação",
                    "total_c_valor": "Valor Total Contratado",
                    "total_c_empenhado": "Valor Empenhado",
                    "tem_contrato": "Contrato Associado",
                }
            ).drop(columns=["mes", "ano"], errors="ignore"),
            width="stretch",
            column_config={
                "Nº Licit.": None,
                "Valor Est. Licitação": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Valor Total Contratado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Valor Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            hide_index=True,
        )

_delta_ext = (
    (_adesao_ext_serie[-1] - _adesao_ext_serie[-2]) / _adesao_ext_serie[-2] * 100
    if len(_adesao_ext_serie) > 1 and _adesao_ext_serie[-2] != 0
    else None
)

ae1, ae2, _, _ = st.columns(4)
with ae1:
    st.metric(
        "Empenhos via Ata Externa",
        adesao_externa["quantidade"],
        delta=f"{_delta_ext:+.1f}%" if _delta_ext is not None else None,
        delta_color="inverse",
        help="Empenhos cuja justificativa contábil referencia uma Ata de Registro de Preços de outro ente (Termo de Adesão Externa).",
    )
    if len(_all_years) >= 2:
        st.plotly_chart(
            sparkline(_all_years, _adesao_ext_serie, "#9C27B0"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_adesao_ext",
        )
with ae2:
    st.metric("Pago via Ata Externa", fmt_compact(adesao_externa["total_pago"]))

if not adesao_externa["lista"].empty:
    with st.expander("Ver empenhos via Ata de Registro de Preços Externa"):
        st.caption(
            "Registros extraídos da justificativa contábil dos empenhos do Fundo Municipal de Saúde "
            "que referenciam explicitamente um Termo de Adesão Externa a Ata de Registro de Preços."
        )
        st.dataframe(
            adesao_externa["lista"].rename(
                columns={
                    "data": "Data",
                    "fornecedor": "Fornecedor",
                    "pago": "Valor Pago",
                    "unidade": "Unidade",
                    "justificativa": "Justificativa Contábil",
                    "num_licitacao": "Nº Licitação",
                }
            ),
            column_config={
                "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Valor Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            width="stretch",
            hide_index=True,
        )

st.subheader("Distribuição por Modalidade")
df_modalidades = dados["contratos_por_modalidade"]
if not df_modalidades.empty and df_modalidades.notna().all().all():
    st.dataframe(
        df_modalidades.rename(
            columns={
                "modalidade": "Modalidade",
                "quantidade": "Qtd",
                "valor_total": "Valor Total",
                "periodo": "Período",
            }
        )
        .sort_values(by=["Modalidade", "Período"], ascending=True)
        .drop(columns=["mes", "ano"], errors="ignore"),
        width="stretch",
        column_config={"Valor Total": st.column_config.NumberColumn(format="R$ %,.2f")},
        hide_index=True,
        column_order=["Período", "Modalidade", "Qtd", "Valor Total"],
    )
    with st.expander(":material/info: O que são essas modalidades?"):
        st.write(f"**Licitação:** {glossary.tooltip('Licitação')}")
        st.write(f"**Pregão Eletrônico:** {glossary.tooltip('Pregão Eletrônico')}")
        st.write(f"**Pregão Presencial:** {glossary.tooltip('Pregão Presencial')}")
        st.write(f"**Dispensa:** {glossary.tooltip('Dispensa de Licitação')}")
        st.write(f"**Inexigibilidade:** {glossary.tooltip('Inexigibilidade')}")
        st.write(f"**Adesão de Ata:** {glossary.tooltip('Adesão de Ata (Carona)')}")

st.subheader("Contratos sem Licitação acima de R$ 62.725,59")
st.caption(
    "[Lei 14.133/21, Art. 75, I](https://licitacoesecontratos.tcu.gov.br/5-10-2-1-dispensa-em-razao-do-valor-incisos-i-e-ii-2/)"
)
lacunas_saude = dados["licitacao_gaps"]
if not lacunas_saude.empty and lacunas_saude.notna().all().all():
    _delta_licit = (
        (_licit_serie[-1] - _licit_serie[-2]) / _licit_serie[-2] * 100
        if len(_licit_serie) > 1 and _licit_serie[-2] != 0
        else None
    )
    lc1, _, _, _ = st.columns(4)
    with lc1:
        st.metric(
            "Contratos s/ licitação",
            len(lacunas_saude),
            delta=f"{_delta_licit:+.1f}%" if _delta_licit is not None else None,
            delta_color="inverse",
        )
        if len(_all_years) >= 2:
            st.plotly_chart(
                sparkline(_all_years, _licit_serie, "#E91E63"),
                use_container_width=True,
                config=SPARK_CFG,
                key="spark_licit_gaps",
            )
    st.dataframe(
        lacunas_saude.rename(
            columns={
                "periodo": "Período",
                "numero": "Nº",
                "fornecedor": "Fornecedor",
                "objeto": "Objeto",
                "valor_contrato": "Valor",
                "modalidade": "Modalidade",
            }
        )
        .sort_values(by="Valor", ascending=False)
        .drop(columns=["mes", "ano"], errors="ignore"),
        width="stretch",
        column_config={"Nº": None, "Valor": st.column_config.NumberColumn(format="R$ %,.2f")},
        hide_index=True,
        column_order=["Período", "Nº", "Fornecedor", "Objeto", "Valor", "Modalidade"],
    )
else:
    st.success("Nenhum contrato acima do limite legal sem processo licitatório.")

if not dados["fracionamento"].empty and dados["fracionamento"].notna().all().all():
    st.subheader(":material/warning: Possível fracionamento de contratos")
    st.dataframe(
        dados["fracionamento"].rename(columns={"periodo": "Período"}).drop(columns=["mes", "ano"], errors="ignore"),
        width="stretch",
        hide_index=True,
    )

st.page_link("pages/licitacoes.py", label="Ver detalhes em Licitações e Contratos →", icon=":material/arrow_forward:")

# ── Seção 4: Quem recebeu ────────────────────────────────────────────────────
st.header("④ Quem recebeu")
hhi1, _, _, _ = st.columns(4)
with hhi1:
    st.metric(
        "Concentração (HHI)",
        f"{dados['hhi']:,.0f}",
        delta=pct_delta(_hhi_serie) if len(_hhi_serie) >= 2 else None,
        delta_color="inverse",
        help="Índice Herfindahl-Hirschman. Acima de 2.500 = concentração alta.",
    )
    if len(_hhi_serie) >= 2:
        st.plotly_chart(
            sparkline(_all_years, _hhi_serie, "#E91E63"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_hhi",
        )
if not dados["principais_fornecedores"].empty and dados["principais_fornecedores"].notna().all().all():
    st.subheader("Top 10 Fornecedores")

    st.dataframe(
        dados["principais_fornecedores"].rename(
            columns={"descricao": "Fornecedor", "empenhado": "Empenhado", "percentual": "%"}
        ),
        width="stretch",
        column_config={
            "codigo": None,
            "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            "%": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True,
    )

    st.subheader("Top Fornecedores e seus Objetos de Contrato")
    df_servicos = dados["principais_fornecedores_servicos"]
    nomes_top_fornecedores = dados["principais_fornecedores"]["descricao"].unique()

    top_servicos = historia_saude.get_principais_servicos_por_fornecedor(df_servicos, nomes_top_fornecedores)

    st.dataframe(
        top_servicos.rename(
            columns={
                "fornecedor": "Fornecedor",
                "objeto": "Objeto / Serviço",
                "total": "Valor Contratado",
            }
        ),
        width="stretch",
        column_config={"Valor Contratado": st.column_config.NumberColumn(format="R$ %,.2f")},
        hide_index=True,
    )

st.page_link("pages/licitacoes.py", label="Ver detalhes em Licitações e Contratos →", icon=":material/arrow_forward:")

# ── Seção 5: Insumos e Assistência Farmacêutica ────────────────────────────────
st.header("⑤ Insumos e Assistência Farmacêutica")

st.subheader("Medicamentos e Insumos (Subfunção 10.303 — Material de Consumo)")
pharma = dados["pharma_empenhos"]
ph1, _, _, _ = st.columns(4)
with ph1:
    st.metric(
        "Total Empenhado",
        fmt_compact(pharma["total"]),
        delta=pct_delta(tendencia_farma_ate_ano["empenhado"].tolist()),
        delta_color="off",
        help="Empenhos da Subfunção 10.303 (Suporte Profilático e Terapêutico) com Natureza de Despesa 3.3.90.30 (Material de Consumo).",
    )
    if len(tendencia_farma_ate_ano) >= 2:
        st.plotly_chart(
            sparkline(
                tendencia_farma_ate_ano["ano"].tolist(), tendencia_farma_ate_ano["empenhado"].tolist(), "#9C27B0"
            ),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_pharma_sec",
        )
st.caption(
    "Os valores acima refletem empenhos diretos classificados na Subfunção 10.303 com Natureza de Despesa 3.3.90.30. "
    "Compras de medicamentos e insumos realizadas via **Adesão a Ata de Registro de Preços Externa** estão "
    "contabilizadas separadamente na seção _Como foi contratado_."
)

pharma_trend = pharma["trend"]
if not pharma_trend.empty:
    fig_pharma = px.bar(
        pharma_trend,
        x="ano",
        y="empenhado",
        title="Medicamentos e Insumos — Empenhado por Ano",
        labels={"ano": "Ano", "empenhado": "Empenhado"},
    )
    fig_pharma.update_traces(hovertemplate="Ano: %{x}<br>Empenhado: R$ %{y:,.2f}<extra></extra>")
    fig_pharma.update_layout(yaxis=dict(tickprefix="R$ ", tickformat=",.0f"))
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(fig_pharma, width="stretch")

if not pharma["detail"].empty:
    with st.expander("Ver detalhes por fornecedor"):
        st.dataframe(
            pharma["detail"].rename(
                columns={"fornecedor": "Fornecedor", "descricao": "Descrição", "total": "Empenhado"}
            ),
            width="stretch",
            column_config={"Empenhado": st.column_config.NumberColumn(format="R$ %,.2f")},
            hide_index=True,
        )

st.subheader("Licitações de Medicamentos e Insumos")
pharma_licit = dados["pharma_licitacoes"]
if pharma_licit.empty:
    st.info("Sem licitações de medicamentos ou insumos registradas para este ano.")
else:
    st.dataframe(
        pharma_licit.rename(
            columns={
                "numero": "Nº",
                "objeto": "Objeto",
                "modalidade": "Modalidade",
                "situacao": "Situação",
                "data_abertura": "Data Abertura",
            }
        ).drop(columns=["valor", "valor_num"], errors="ignore"),
        width="stretch",
        column_config={
            "Nº": None,
        },
        hide_index=True,
        column_order=["Nº", "Objeto", "Modalidade", "Situação", "Data Abertura"],
    )

st.subheader(":material/gavel: Judicialização da Saúde")
st.caption(
    "Despesas decorrentes de sentenças judiciais (Elemento 3.3.90.91) do Fundo Municipal de Saúde, "
    "separadas das compras programadas de medicamentos e insumos."
)
pharma_jud = dados["pharma_judicial"]
jud1, _, _, _ = st.columns(4)
with jud1:
    st.metric(
        "Judicialização",
        fmt_compact(pharma_jud["total"]),
        delta=pct_delta(_pharma_jud_serie) if len(_pharma_jud_serie) >= 2 else None,
        delta_color="inverse",
        help="Empenhos com Elemento de Despesa 3.3.90.91 (Sentenças Judiciais) no Fundo Municipal de Saúde.",
    )
    if len(_pharma_jud_serie) >= 2:
        st.plotly_chart(
            sparkline(_all_years, _pharma_jud_serie, "#F44336"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_jud",
        )
if pharma_jud["total"] == 0:
    st.info("Sem registros de judicialização para este ano.")
elif not pharma_jud["detail"].empty:
    with st.expander("Ver detalhes"):
        st.dataframe(
            pharma_jud["detail"].rename(
                columns={
                    "subfuncao": "Subfunção",
                    "fornecedor": "Fornecedor",
                    "descricao": "Descrição",
                    "total": "Empenhado",
                }
            ),
            width="stretch",
            column_config={"Empenhado": st.column_config.NumberColumn(format="R$ %,.2f")},
            hide_index=True,
        )

st.page_link("pages/licitacoes.py", label="Ver detalhes em Licitações e Contratos →", icon=":material/arrow_forward:")

st.divider()
st.caption(f"Fonte: [Portal de Transparência]({constants.PORTAL_URL})")
