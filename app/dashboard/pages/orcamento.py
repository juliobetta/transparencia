import sys
from pathlib import Path
from typing import Any

import constants

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import (
    ANO_ATUAL,
    ANO_INICIAL,
    bar_chart_h,
    fmt_compact,
    funnel_waterfall,
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

from app.analytics import execucao_orcamentaria, orcamento_funcional

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _orcamento(conn, year, empresa_ids, _extracted_at):
    return execucao_orcamentaria.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _orcamento_by_year(conn, years, empresa_ids, _extracted_at):
    return execucao_orcamentaria.summarize_by_year(conn, list(years), empresa_ids=empresa_ids)


conn = get_conn()
year, empresa_ids = render_sidebar()
_extracted_at = get_data_extracao(conn)

_partial_suffix = f"parcial, Jan–{partial_year_month(_extracted_at)}" if year == ANO_ATUAL else ""
_eyebrow = f"Administrativo · Exercício {year}" + (f" ({_partial_suffix})" if _partial_suffix else "")
st.html(
    page_header(
        _eyebrow,
        "Execução Orçamentária",
        "Cada real passa por quatro estágios legais antes de sair do caixa: "
        "<strong style='color:#1a1d21'>reservar</strong> (empenho), "
        "<strong style='color:#1a1d21'>confirmar a entrega</strong> (liquidação) e "
        "<strong style='color:#1a1d21'>pagar</strong>. Veja quanto do orçamento já avançou em cada etapa.",
    )
)

if year == ANO_ATUAL:
    render_aviso_ano_parcial(year, _extracted_at)

df_orcamento = _orcamento(conn, year, empresa_ids, _extracted_at)
totais = execucao_orcamentaria.summarize(df_orcamento)

_all_years = list(range(ANO_INICIAL, year + 1))
_hist = _orcamento_by_year(conn, tuple(_all_years), empresa_ids, _extracted_at)
_anos = _all_years
_dotacao_serie = [_hist[y]["total_dotacao"] for y in _anos]
_empenhado_serie = [_hist[y]["total_empenhado"] for y in _anos]
_liquidado_serie = [_hist[y]["total_liquidado"] for y in _anos]
_pago_serie = [_hist[y]["total_pago"] for y in _anos]

_dot = totais["total_dotacao"]
_emp = totais["total_empenhado"]
_liq = totais["total_liquidado"]
_pago = totais["total_pago"]
_pct_emp = _emp / _dot if _dot > 0 else 0.0
_pct_liq = _liq / _dot if _dot > 0 else 0.0
_pct_pago = _pago / _dot if _dot > 0 else 0.0

st.html(
    kpi_grid(
        kpi_card("Dotação Atualizada", fmt_compact(_dot), sub=pct_delta(_dotacao_serie) or ""),
        kpi_card("Total Empenhado", fmt_compact(_emp), sub=f"{_pct_emp:.1%} da dotação", accent=True),
        kpi_card("Total Liquidado", fmt_compact(_liq), sub=f"{_pct_liq:.1%} da dotação", accent=True),
        kpi_card("Total Pago", fmt_compact(_pago), sub=f"{_pct_pago:.1%} da dotação", accent=True),
        cols=4,
    )
)

st.html(section_heading("Funil da execução"))
st.html(
    funnel_waterfall(
        [
            ("Dotação", _dot, fmt_compact(_dot)),
            ("Empenhado", _emp, fmt_compact(_emp)),
            ("Liquidado", _liq, fmt_compact(_liq)),
            ("Pago", _pago, fmt_compact(_pago)),
        ],
        _dot,
    )
)

df_funcional = orcamento_funcional.get_orcamento_funcional(conn, year, empresa_ids=empresa_ids)
df_funcional_resumo = (
    df_funcional.groupby("funcao_nome")[["dotacao_atualizada", "empenhado", "liquidado", "pago"]]
    .sum()
    .reset_index()
    .sort_values("pago", ascending=False)
)

st.html(section_heading("Para onde vai o gasto, por função", aside="valor pago · R$ mi"))
if not df_funcional_resumo.empty:
    _func_rows = [
        (str(r["funcao_nome"]), float(r["pago"]), fmt_compact(float(r["pago"])))
        for _, r in df_funcional_resumo.head(8).iterrows()
    ]
    st.html(bar_chart_h(_func_rows))

st.caption(f"[Ver no portal oficial →]({constants.PORTAL_URL})")
