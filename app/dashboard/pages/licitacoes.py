import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import (
    ANO_ATUAL,
    ANO_INICIAL,
    bar_chart_h,
    dense_table,
    fmt_currency,
    get_conn,
    get_data_extracao,
    kpi_card,
    kpi_grid,
    page_header,
    partial_year_month,
    pct_delta,
    render_aviso_ano_parcial,
    render_sidebar,
    section_heading,
)
from sqlalchemy.engine import Engine

import constants
import db
from app.analytics import adesao_de_ata, anomalias_contratuais, licitacao_gaps
from app.analytics import contratos as contratos_analysis
from app.analytics.constants import THRESHOLD_COMPRAS_SERVICOS

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _lacunas_licitacao(conn, year, empresa_ids, _extracted_at):
    return licitacao_gaps.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao(conn, year, empresa_ids, _extracted_at):
    return adesao_de_ata.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_externa(conn, year, empresa_ids, _extracted_at):
    return adesao_de_ata.run_external(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _anomalias(conn, year, empresa_ids, _extracted_at):
    return anomalias_contratuais.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _acima_por_ano(conn, years, empresa_ids, _extracted_at):
    return licitacao_gaps.counts_by_year(conn, list(years), empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _totals_sem_lic_por_ano(conn, years, empresa_ids, _extracted_at):
    return licitacao_gaps.totals_sem_licitacao_por_ano(conn, list(years), empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_por_ano(conn, years, empresa_ids, _extracted_at):
    return adesao_de_ata.formal_counts_by_year(conn, list(years), empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_ext_por_ano(conn, years, empresa_ids, _extracted_at):
    return adesao_de_ata.external_counts_by_year(conn, list(years), empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _modalidade(conn, year, empresa_ids, _extracted_at):
    return contratos_analysis.distribuicao_modalidade(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _fundlegal(conn, year, empresa_ids, _extracted_at):
    return contratos_analysis.distribuicao_fundamento_legal(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _top_fornecedores(conn, year, empresa_ids, _extracted_at):
    return contratos_analysis.top_fornecedores(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _baixa_execucao(conn, year, empresa_ids, _extracted_at):
    return contratos_analysis.contratos_baixa_execucao(conn, year, empresa_ids=empresa_ids)


conn = get_conn()
_orgaos = db.get_empresas(conn)
year, empresa_ids = render_sidebar()
_extracted_at = get_data_extracao(conn)

lacunas = _lacunas_licitacao(conn, year, empresa_ids, _extracted_at)
adesao = _adesao(conn, year, empresa_ids, _extracted_at)
adesao_externa = _adesao_externa(conn, year, empresa_ids, _extracted_at)
anomalias = _anomalias(conn, year, empresa_ids, _extracted_at)
df_modalidade = _modalidade(conn, year, empresa_ids, _extracted_at)
df_fundlegal = _fundlegal(conn, year, empresa_ids, _extracted_at)
df_top_forn = _top_fornecedores(conn, year, empresa_ids, _extracted_at)
df_baixa_exec = _baixa_execucao(conn, year, empresa_ids, _extracted_at)

acima = licitacao_gaps.filter_above_limit(lacunas)
saude = licitacao_gaps.filter_above_limit_health(lacunas)

_all_years = list(range(ANO_INICIAL, year + 1))
_anos = _all_years
_hist_acima = _acima_por_ano(conn, tuple(_all_years), empresa_ids, _extracted_at)
_hist_totals = _totals_sem_lic_por_ano(conn, tuple(_all_years), empresa_ids, _extracted_at)
_hist_adesao = _adesao_por_ano(conn, tuple(_all_years), empresa_ids, _extracted_at)
_hist_adesao_ext = _adesao_ext_por_ano(conn, tuple(_all_years), empresa_ids, _extracted_at)

_acima_serie = [_hist_acima[y] for y in _anos]
_totals_serie = [_hist_totals[y] for y in _anos]
_limite_fmt = fmt_currency(THRESHOLD_COMPRAS_SERVICOS)
_adesao_serie = [_hist_adesao[y] for y in _anos]
_adesao_ext_serie = [_hist_adesao_ext[y] for y in _anos]

_partial_suffix = f"parcial, Jan–{partial_year_month(_extracted_at)}" if year == ANO_ATUAL else ""
_eyebrow = f"Administrativo · Exercício {year}" + (f" ({_partial_suffix})" if _partial_suffix else "")
st.html(
    page_header(
        _eyebrow,
        "Licitações e Contratos",
        "Contratos sem licitação são comuns e frequentemente legais — dispensas de baixo valor e inexigibilidades "
        "são permitidas por lei. O ponto de atenção são os contratos <strong style='color:#1a1d21'>acima de "
        f"{_limite_fmt} sem licitação</strong>, que exigem justificativa formal.",
    )
)

if year == ANO_ATUAL:
    render_aviso_ano_parcial(year, _extracted_at)

st.html(
    kpi_grid(
        kpi_card(
            "Acima do limite s/ licitação", str(len(acima)), sub=pct_delta(_acima_serie) or "", risk=len(acima) > 0
        ),
        kpi_card("Total sem processo licitatório", str(len(lacunas)), sub=pct_delta(_totals_serie) or ""),
        kpi_card("Adesões de Ata (carona)", str(_hist_adesao[year]), sub=pct_delta(_adesao_serie) or ""),
        kpi_card("Empenhos via Ata Externa", str(adesao_externa["quantidade"]), sub=pct_delta(_adesao_ext_serie) or ""),
        cols=4,
    )
)
st.html(section_heading("Distribuição por modalidade", aside="valor contratado · R$ mi"))
if not df_modalidade.empty:
    _mod_rows = [
        (str(r["modalidade"]), float(r["valor"]), f"R$ {r['valor'] / 1e6:.1f}mi · {int(r['contratos'])}")
        for _, r in df_modalidade.sort_values("valor", ascending=False).iterrows()
    ]
    st.html(bar_chart_h(_mod_rows))

if not df_fundlegal.empty:
    st.html(section_heading("Por fundamento legal"))
    _fund_rows = [
        (str(r["fundlegal"]), float(r["valor"]), f"R$ {r['valor'] / 1e6:.1f}mi · {int(r['contratos'])}")
        for _, r in df_fundlegal.sort_values("valor", ascending=False).iterrows()
    ]
    st.html(bar_chart_h(_fund_rows))

# ── Contratos acima do limite — dense table ───────────────────────────────────
st.html(section_heading("Contratos acima do limite, sem licitação"))
if not acima.empty:
    _modality_kind: dict[str, str] = {
        "Dispensa": "dispensa",
        "Inexigibilidade": "inexigibilidade",
        "Pregão": "pregao",
        "Concorrência": "concorrencia",
        "Adesão a ata": "adesao",
    }
    _frac_fornecedores: set = set(
        anomalias["fracionamento"]["fornecedor"].tolist() if not anomalias["fracionamento"].empty else []
    )
    _search_acima = st.text_input(
        "Buscar contrato…", placeholder="Fornecedor ou objeto", label_visibility="collapsed", key="search_acima"
    )
    _df_acima = (
        acima
        if not _search_acima
        else acima[
            acima["fornecedor"].str.contains(_search_acima, case=False, na=False)
            | acima["objeto"].str.contains(_search_acima, case=False, na=False)
        ]
    )
    _rows_acima = [
        [
            row["fornecedor"]
            + (
                '<div style="font-size:10.5px;color:oklch(0.6 0.13 55);margin-top:2px">⚠ possível fracionamento</div>'
                if row["fornecedor"] in _frac_fornecedores
                else ""
            ),
            str(row["objeto"])[:80] + ("…" if len(str(row["objeto"])) > 80 else ""),
            {"label": str(row["modalidade"]), "kind": _modality_kind.get(str(row["modalidade"]), "default")},
            fmt_currency(float(row["valor_contrato"])),
            str(row["periodo"]),
        ]
        for _, row in _df_acima.iterrows()
    ]
    st.html(
        dense_table(
            ["Fornecedor", "Objeto", "Modalidade", "Valor", "Período"],
            _rows_acima,
            footer=f"Mostrando {len(_df_acima)} de {len(acima)} contratos",
        )
    )
else:
    st.caption("Nenhum contrato acima do limite sem licitação identificado para este ano.")

# ── Detalhamento completo ─────────────────────────────────────────────────────
with st.expander("Ver todos os contratos sem processo licitatório"):
    df_exibir = lacunas.rename(
        columns={
            "fornecedor": "Fornecedor",
            "objeto": "Objeto",
            "valor_contrato": "Valor",
            "periodo": "Período",
            "modalidade": "Modalidade",
            "fundlegal": "Fundamento Legal",
        }
    )
    st.dataframe(
        df_exibir[["Fornecedor", "Objeto", "Modalidade", "Fundamento Legal", "Valor", "Período"]],
        column_config={"Valor": st.column_config.NumberColumn(format="R$ %,.2f")},
        width="stretch",
        hide_index=True,
    )

with st.expander("Ver licitações via Adesão de Ata"):
    if not adesao["lista"].empty:
        df_adesao = (
            adesao["lista"]
            .rename(
                columns={
                    "objeto": "Objeto",
                    "periodo": "Período",
                    "licitacao_valor": "Valor Est. Licitação",
                    "total_c_valor": "Valor Total Contratado",
                    "total_c_empenhado": "Valor Empenhado",
                    "tem_contrato": "Contrato Associado",
                }
            )
            .drop(columns=["numero"], errors="ignore")
        )
        st.dataframe(
            df_adesao[
                [
                    "Objeto",
                    "Período",
                    "Valor Est. Licitação",
                    "Valor Total Contratado",
                    "Valor Empenhado",
                    "Contrato Associado",
                ]
            ],
            column_config={
                "Valor Est. Licitação": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Valor Total Contratado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Valor Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Nenhuma adesão de ata registrada para este ano.")

with st.expander("Ver empenhos via Ata de Registro de Preços Externa"):
    if not adesao_externa["lista"].empty:
        _ext_exib = adesao_externa["lista"].copy()
        _ext_exib["unidade"] = _ext_exib["unidade"].astype(str).map(_orgaos).fillna(_ext_exib["unidade"])
        st.dataframe(
            _ext_exib.rename(
                columns={
                    "data": "Data",
                    "fornecedor": "Fornecedor",
                    "empenhado": "Valor Empenhado",
                    "pago": "Valor Pago",
                    "unidade": "Entidade",
                    "justificativa": "Justificativa Contábil",
                    "num_licitacao": "Nº Licitação",
                }
            ),
            column_config={
                "Valor Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Valor Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
            },
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Nenhum empenho com referência a ata externa registrado para este ano.")

# ── Top Fornecedores ──────────────────────────────────────────────────────────
with st.expander("Ver top fornecedores por valor contratado"):
    if not df_top_forn.empty:
        st.dataframe(
            df_top_forn.rename(
                columns={
                    "fornecedor_nome": "Fornecedor",
                    "contratos": "Nº Contratos",
                    "valor_total": "Valor Total",
                    "empenhado_total": "Valor Empenhado",
                }
            ),
            column_config={
                "Valor Total": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Valor Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Sem dados de fornecedores para este ano.")

# ── Contratos com Baixa Execução ──────────────────────────────────────────────
with st.expander("Ver contratos com baixa execução (< 20%)"):
    if not df_baixa_exec.empty:
        st.caption(
            "Contratos onde o valor empenhado é inferior a 20% do valor contratado. "
            "Pode indicar contratos parados, subdimensionados ou com execução atrasada."
        )
        _baixa_exib = df_baixa_exec.copy()
        _baixa_exib["empresa_id"] = _baixa_exib["empresa_id"].astype(str).map(_orgaos).fillna(_baixa_exib["empresa_id"])
        st.dataframe(
            _baixa_exib.rename(
                columns={
                    "empresa_id": "Entidade",
                    "contrato_numero": "Nº Contrato",
                    "fornecedor_nome": "Fornecedor",
                    "objeto": "Objeto",
                    "valor_contrato": "Valor",
                    "empenhado": "Empenhado",
                    "pct_execucao": "% Execução",
                }
            ),
            column_config={
                "Valor": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "% Execução": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
            },
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Nenhum contrato com baixa execução identificado para este ano.")

st.caption(f"[Ver no portal oficial →]({constants.PORTAL_URL})")
