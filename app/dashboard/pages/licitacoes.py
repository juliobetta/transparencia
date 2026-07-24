import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import (
    ANO_ATUAL,
    ANO_INICIAL,
    alert_box,
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


conn = get_conn()
_orgaos = db.get_empresas(conn)
year, empresa_ids = render_sidebar()
_extracted_at = get_data_extracao(conn)

lacunas = _lacunas_licitacao(conn, year, empresa_ids, _extracted_at)
adesao = _adesao(conn, year, empresa_ids, _extracted_at)
adesao_externa = _adesao_externa(conn, year, empresa_ids, _extracted_at)
anomalias = _anomalias(conn, year, empresa_ids, _extracted_at)
df_modalidade = _modalidade(conn, year, empresa_ids, _extracted_at)

acima = licitacao_gaps.filter_above_limit(lacunas)

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
if not anomalias["fracionamento"].empty:
    _n_frac = len(anomalias["fracionamento"]["fornecedor"].unique())
    st.html(
        alert_box(
            f"<strong>{_n_frac} caso{'s' if _n_frac != 1 else ''} de possível fracionamento.</strong> "
            "Fornecedores com 3 ou mais contratos próximos ao limite de dispensa no mesmo órgão, "
            "sugerindo divisão artificial de compras para evitar licitação.",
            kind="warning",
        )
    )

st.html(section_heading("Distribuição por modalidade", aside="valor contratado · R$ mi"))
if not df_modalidade.empty:
    _mod_rows = [
        (str(r["modalidade"]), float(r["valor"]), f"R$ {r['valor'] / 1e6:.1f}mi · {int(r['contratos'])}")
        for _, r in df_modalidade.sort_values("valor", ascending=False).iterrows()
    ]
    st.html(bar_chart_h(_mod_rows))

# ── Contratos acima do limite — dense table ───────────────────────────────────
st.html(
    section_heading(
        "Contratos acima do limite, sem licitação", aside=f"{len(acima)} contratos · exige justificativa formal"
    )
)
if not acima.empty:
    st.html(
        f'<p style="font-size:12.5px;color:#6b7280;margin:0 0 16px;max-width:70ch">'
        f"Cada linha merece análise da justificativa oficial. Quando o mesmo fornecedor aparece várias vezes "
        f"com valores próximos ao teto de {_limite_fmt}, pode indicar "
        f'<strong style="color:#1a1d21">fracionamento</strong>.</p>'
    )
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

st.caption(f"[Ver no portal oficial →]({constants.PORTAL_URL})")
