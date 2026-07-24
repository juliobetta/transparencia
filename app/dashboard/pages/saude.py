import sys
from pathlib import Path
from typing import Any

import pandas as pd

import constants

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import (
    ANO_ATUAL,
    donut_conic,
    fmt_compact,
    get_conn,
    get_data_extracao,
    kpi_card,
    kpi_grid,
    page_header,
    partial_year_month,
    pct_delta,
    plotly_card_end,
    plotly_card_layout,
    plotly_card_start,
    render_aviso_ano_parcial,
    render_sidebar,
    section_heading,
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

_partial_suffix = f"parcial, Jan–{partial_year_month(_extracted_at)}" if year == ANO_ATUAL else ""
_eyebrow = f"Temas · Exercício {year}" + (f" ({_partial_suffix})" if _partial_suffix else "")

col_header, col_pdf = st.columns([7, 1])
with col_header:
    st.html(
        page_header(
            _eyebrow,
            "Fundo Municipal de Saúde",
            "Acompanha o dinheiro do Fundo Municipal de Saúde do começo ao fim: "
            "<strong style='color:#1a1d21'>o que entrou</strong>, o que foi empenhado, como foi contratado e quem recebeu.",
        )
    )
with col_pdf:
    pdf_bytes = _pdf(conn, year, _extracted_at)
    st.download_button(
        label="Baixar PDF",
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

_tend_anos = tendencia_ate_ano["ano"].tolist()
st.html(
    kpi_grid(
        kpi_card(
            "Dotação Atualizada",
            fmt_compact(orcamento["dotacao"]),
            sub=pct_delta(tendencia_ate_ano["dotacao"].tolist()) or "",
        ),
        kpi_card(
            "Total Empenhado",
            fmt_compact(orcamento["empenhado"]),
            sub=pct_delta(tendencia_ate_ano["empenhado"].tolist()) or "",
            accent=True,
        ),
        kpi_card(
            "Taxa de Execução",
            f"{orcamento['taxa_execucao']:.1%}",
            sub=pct_delta(tendencia_ate_ano["taxa"].tolist()) or "",
            accent=True,
        ),
        kpi_card(
            "Medicamentos e Insumos",
            fmt_compact(dados["pharma_empenhos"]["total"]),
            sub=pct_delta(tendencia_farma_ate_ano["empenhado"].tolist()) or "",
        ),
        cols=4,
    )
)
# ── Seção 1: O que entrou ───────────────────────────────────────────────────
st.html(section_heading("O que entrou no Fundo", numbered="①"))

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
else:
    rp1.info("Sem repasses registrados para este ano.")

st.subheader("Fontes de Receita do Fundo")
if not receita_saude.empty:
    _rec_row = (
        receita_saude[receita_saude["ano"] == year].iloc[0]
        if year in receita_saude["ano"].values
        else receita_saude.iloc[-1]
    )
    _rec_propria = float(_rec_row["receita_propria"])
    _rec_uniao = float(_rec_row["transferencias_uniao"])
    _rec_estado = float(_rec_row["transferencias_estado"])
    _rec_total = _rec_propria + _rec_uniao + _rec_estado
    if _rec_total > 0:
        _pct_propria = _rec_propria / _rec_total * 100
        _pct_uniao = _rec_uniao / _rec_total * 100
        _pct_estado = _rec_estado / _rec_total * 100
        _rec_col, _kpi_col = st.columns([1, 1])
        with _rec_col:
            st.html(
                donut_conic(
                    [
                        ("Receita Própria", _pct_propria, "oklch(0.52 0.13 250)"),
                        ("Transferências União", _pct_uniao, "oklch(0.5 0.13 145)"),
                        ("Transferências Estado", _pct_estado, "oklch(0.55 0.13 55)"),
                    ],
                    center_label=f"{_pct_uniao + _pct_estado:.0f}%",
                    center_sub="repasses externos",
                )
            )
        with _kpi_col:
            st.html(
                kpi_grid(
                    kpi_card("Receita Própria", fmt_compact(_rec_propria), sub=f"{_pct_propria:.0f}% do total"),
                    kpi_card("Transf. União", fmt_compact(_rec_uniao), sub=f"{_pct_uniao:.0f}% do total"),
                    kpi_card("Transf. Estado", fmt_compact(_rec_estado), sub=f"{_pct_estado:.0f}% do total"),
                    cols=3,
                )
            )
    st.caption(
        "Composição da receita do Fundo Municipal de Saúde — revela dependência de transferências federais "
        "(SUS, PAB, etc.) vs receita própria."
    )

st.page_link("pages/receitas.py", label="Ver detalhes em Fontes de Receita →", icon=":material/arrow_forward:")

# ── Seção 2: O que foi gasto ────────────────────────────────────────────────
st.html(section_heading("O que foi empenhado", numbered="②"))
st.subheader("Evolução do Empenhado por Ano")
tendencia_execucao = dados["tendencia_execucao"]
if not tendencia_execucao.empty:
    fig = px.bar(
        tendencia_execucao,
        x="ano",
        y="empenhado",
        labels={"ano": "Ano", "empenhado": "Empenhado"},
        color_discrete_sequence=["oklch(0.52 0.13 250)"],
    )
    fig.update_traces(hovertemplate="Ano: %{x}<br>Empenhado: R$ %{y:,.0f}<extra></extra>", marker_line_width=0)
    fig.update_layout(
        **plotly_card_layout("Fundo de Saúde — Empenhado por Ano", height=300),
        xaxis=dict(dtick=1, tickformat="d"),
        yaxis=dict(tickprefix="R$ ", tickformat=",.0f"),
    )
    st.html(plotly_card_start())
    st.plotly_chart(fig, use_container_width=True)
    st.html(plotly_card_end())

    st.dataframe(
        tendencia_execucao.rename(columns={"ano": "Ano", "empenhado": "Empenhado"}),
        width="stretch",
        hide_index=True,
        column_config={
            "Ano": st.column_config.NumberColumn(format="%d"),
            "Empenhado": st.column_config.NumberColumn(format="R$ %,.0f"),
        },
    )

# ── Seção 3: Insumos e Assistência Farmacêutica ────────────────────────────────
st.html(section_heading("Insumos e Assistência Farmacêutica", numbered="③"))

st.subheader("Medicamentos e Insumos (Subfunção 10.303 — Material de Consumo)")
pharma = dados["pharma_empenhos"]
_pct_pharma = pharma["total"] / orcamento["empenhado"] if orcamento["empenhado"] > 0 else 0.0
st.html(
    kpi_grid(
        kpi_card(
            "Medicamentos e Insumos",
            fmt_compact(pharma["total"]),
            sub=pct_delta(tendencia_farma_ate_ano["empenhado"].tolist()) or "",
            accent=True,
        ),
        kpi_card(
            "% do Total Empenhado",
            f"{_pct_pharma:.1%}",
            sub="participação no orçamento",
        ),
        kpi_card(
            "Judicialização",
            fmt_compact(dados["pharma_judicial"]["total"]),
            sub="sentenças judiciais (3.3.90.91)",
            risk=dados["pharma_judicial"]["total"] > 0,
        ),
        cols=3,
    )
)
st.caption(
    "Os valores acima refletem empenhos diretos classificados na Subfunção 10.303 com Natureza de Despesa 3.3.90.30. "
    "Compras de medicamentos e insumos realizadas via **Adesão a Ata de Registro de Preços Externa** estão "
    "contabilizadas separadamente em Licitações e Contratos."
)

pharma_trend = pharma["trend"]
if not pharma_trend.empty:
    fig_pharma = px.bar(
        pharma_trend,
        x="ano",
        y="empenhado",
        labels={"ano": "Ano", "empenhado": "Empenhado"},
        color_discrete_sequence=["oklch(0.52 0.13 250)"],
    )
    fig_pharma.update_traces(hovertemplate="Ano: %{x}<br>Empenhado: R$ %{y:,.0f}<extra></extra>", marker_line_width=0)
    fig_pharma.update_layout(
        **plotly_card_layout("Medicamentos e Insumos — Empenhado por Ano", height=280),
        xaxis=dict(dtick=1, tickformat="d"),
        yaxis=dict(tickprefix="R$ ", tickformat=",.0f"),
    )
    st.html(plotly_card_start())
    st.plotly_chart(fig_pharma, use_container_width=True)
    st.html(plotly_card_end())

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
