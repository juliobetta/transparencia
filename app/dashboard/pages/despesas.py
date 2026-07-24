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
    donut_conic,
    fmt_compact,
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

from app.analytics import analise_despesas, concentracao_fornecedores, posicao_fiscal
from app.analytics.posicao_fiscal import resumo_pendentes

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _impacto(conn, year, empresa_ids, _extracted_at, cidade_clean: str = ""):
    return analise_despesas.get_impacto_gastos_locais(conn, year, empresa_ids=empresa_ids, cidade_clean=cidade_clean)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _concentracao(conn, year, empresa_ids, _extracted_at):
    return concentracao_fornecedores.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _fornecedores_pendentes(conn, year, empresa_ids, _extracted_at):
    return posicao_fiscal.get_fornecedores_pendentes(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _impacto_por_ano(conn, years, empresa_ids, _extracted_at):
    return analise_despesas.get_impacto_por_ano(
        conn, list(years), empresa_ids=empresa_ids, cidade_clean=_config.cidade_clean
    )


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _tendencia_pendentes(conn, years, empresa_ids, _extracted_at):
    return posicao_fiscal.get_tendencia_fornecedores_pendentes(conn, list(years), empresa_ids=empresa_ids)


conn = get_conn()
year, empresa_ids = render_sidebar()
_extracted_at = get_data_extracao(conn)
_config = st.session_state["portal_config"]
_local_label = f"Negócios Locais ({_config.display_name})"

_all_years = list(range(ANO_INICIAL, year + 1))
_hist_impacto = _impacto_por_ano(conn, tuple(_all_years), empresa_ids, _extracted_at)
_hist_pendentes = _tendencia_pendentes(conn, tuple(_all_years), empresa_ids, _extracted_at)

_partial_suffix = f"parcial, Jan–{partial_year_month(_extracted_at)}" if year == ANO_ATUAL else ""
_eyebrow = f"Administrativo · Exercício {year}" + (f" ({_partial_suffix})" if _partial_suffix else "")
st.html(
    page_header(
        _eyebrow,
        "Despesas Detalhadas",
        "Onde e como os recursos são aplicados: quanto fica na economia local, "
        "se há concentração em poucos fornecedores e quais compromissos de anos anteriores ainda não foram pagos.",
    )
)

if year == ANO_ATUAL:
    render_aviso_ano_parcial(year, _extracted_at)

# ── Para onde vai o dinheiro ─────────────────────────────────────────────────
impacto = _impacto(conn, year, empresa_ids, _extracted_at, cidade_clean=_config.cidade_clean)
concentracao = _concentracao(conn, year, empresa_ids, _extracted_at)

_pct_local_serie = [_hist_impacto[y]["pct_local"] for y in _all_years]

st.html(section_heading("Para onde vai o dinheiro", aside="apenas compras, serviços e investimentos"))

_local_pct = float(impacto.get("pct_local", 0))
_ext_pct = 100.0 - _local_pct
_local_val = fmt_compact(float(impacto.get("local_pago", 0)))
_ext_val = fmt_compact(float(impacto.get("externo_pago", 0)))
_col_donut, _col_kpis = st.columns([1.1, 1])
with _col_donut:
    st.html(
        '<div style="background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px 24px;margin-bottom:1rem">'
        + donut_conic(
            [
                ("Empresas locais", _local_pct, "oklch(0.5 0.13 145)", _local_val),
                ("Empresas externas", _ext_pct, "oklch(0.55 0.11 25)", _ext_val),
            ],
            center_label=f"{_local_pct:.0f}%",
            center_sub="local",
        )
        + "</div>"
    )
with _col_kpis:
    st.html(
        kpi_grid(
            kpi_card(
                "Índice de compras locais", f"{_local_pct:.1f}%", sub=pct_delta(_pct_local_serie) or "", accent=True
            ),
            kpi_card("HHI — Concentração", f"{concentracao['hhi']:,.0f}", sub="acima de 2.500 = alta"),
            cols=1,
        )
    )

# ── Restos a Pagar ────────────────────────────────────────────────────────────
st.html(section_heading("Restos a Pagar", aside="obrigações de exercícios anteriores"))

st.html(
    alert_box(
        "<strong>O que são Restos a Pagar?</strong> São despesas que a prefeitura empenhou (reservou) em anos anteriores "
        "mas ainda não pagou. Não são contas atrasadas do ano atual — são compromissos legais de exercícios "
        "passados que continuam válidos até serem pagos ou cancelados.",
        kind="info",
    )
)

df_pendentes = _fornecedores_pendentes(conn, year, empresa_ids, _extracted_at)
if not df_pendentes.empty:
    resumo = resumo_pendentes(df_pendentes)
    _val_pendentes = _hist_pendentes["total_pendente"].tolist() if not _hist_pendentes.empty else []
    _cnt_pendentes = _hist_pendentes["num_fornecedores"].tolist() if not _hist_pendentes.empty else []

    st.html(
        kpi_grid(
            kpi_card("Total Pendente", fmt_compact(resumo["total"]), sub=pct_delta(_val_pendentes) or "", risk=True),
            kpi_card("Fornecedores Aguardando", str(resumo["count"]), sub=pct_delta(_cnt_pendentes) or ""),
            kpi_card("Dívida mais antiga desde", str(resumo["oldest"])),
            cols=3,
        )
    )

    _amber_steps = ["oklch(0.55 0.11 25)", "oklch(0.6 0.11 30)", "oklch(0.66 0.1 40)", "oklch(0.72 0.1 55)", "#c7ccd4"]
    _top_pend = df_pendentes.nlargest(5, "pendente")
    if not _top_pend.empty:
        _max_pend = float(_top_pend["pendente"].max())
        _pend_items = "".join(
            f'<div style="display:flex;align-items:center;gap:14px">'
            f'<span style="width:180px;font-size:12.5px;color:#4b5563;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{row["descricao"]}</span>'
            f'<div style="flex:1;height:18px;background:#eef0f4;border-radius:4px;overflow:hidden">'
            f'<div style="width:{float(row["pendente"]) / _max_pend * 100:.1f}%;height:100%;background:{_amber_steps[min(i, 4)]};border-radius:4px"></div></div>'
            f"<span style=\"width:80px;min-width:80px;text-align:right;font-family:'Source Serif 4',serif;font-weight:700;font-size:13px\">{fmt_compact(float(row['pendente']))}</span>"
            f"</div>"
            for i, (_, row) in enumerate(_top_pend.iterrows())
        )
        st.html(
            f'<div style="background:var(--card);border:1px solid var(--line);border-radius:14px;'
            f'padding:22px 26px;display:flex;flex-direction:column;gap:13px;margin-bottom:1.5rem">'
            f'<div style="font-size:12px;color:var(--muted);margin-bottom:4px">Fornecedores com maior pendência</div>'
            f"{_pend_items}</div>"
        )
else:
    st.html(alert_box("Nenhum fornecedor com pagamento pendente para este exercício.", kind="info"))
