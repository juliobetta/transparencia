import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import (
    ANO_ATUAL,
    ANO_INICIAL,
    alert_box,
    barra_comparativa,
    fmt_compact,
    get_conn,
    get_data_extracao,
    kpi_card,
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

import constants
from app.analytics import fontes_receita, posicao_fiscal

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _receita(conn, years, empresa_ids, _extracted_at):
    return fontes_receita.run(conn, list(years), empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _posicao_fiscal(conn, year, empresa_ids, _extracted_at, _v=6):
    return posicao_fiscal.run(conn, year, empresa_ids=empresa_ids)


conn = get_conn()
year, empresa_ids = render_sidebar()
_extracted_at = get_data_extracao(conn)

_partial_suffix = f"parcial, Jan–{partial_year_month(_extracted_at)}" if year == ANO_ATUAL else ""
_eyebrow = f"Administrativo · Exercício {year}" + (f" ({_partial_suffix})" if _partial_suffix else "")
st.html(
    page_header(
        _eyebrow,
        "Fontes de Receita",
        "Compara o que a prefeitura <strong style='color:#1a1d21'>planejou arrecadar</strong> "
        "(previsão da LOA) com o que <strong style='color:#1a1d21'>efetivamente entrou</strong> no caixa, por origem do recurso.",
    )
)

_all_years = list(range(ANO_INICIAL, year + 1))
df_hist = _receita(conn, tuple(_all_years), empresa_ids, _extracted_at)
df_ano = df_hist[df_hist["ano"] == year]

_tem_arrecadado = not df_ano.empty and df_ano.iloc[0]["total_arrecadado"] > 0

if _tem_arrecadado:
    if year == ANO_ATUAL:
        render_aviso_ano_parcial(year, _extracted_at)
else:
    st.html(
        alert_box(
            "Dados de arrecadação efetiva ainda não disponíveis para este exercício. Exibindo apenas a previsão orçamentária.",
            kind="info",
        )
    )

if not df_ano.empty:
    row = df_ano.iloc[0]
    _prev_serie = df_hist["total_previsto"].tolist()
    _total_serie = df_hist["total"].tolist()

    c1, c2 = st.columns(2)
    with c1:
        st.html(
            kpi_card(
                "Previsão Orçamentária (LOA)",
                fmt_compact(float(row["total_previsto"])),
                sub=pct_delta(_prev_serie) or "",
            )
        )
    with c2:
        if _tem_arrecadado:
            st.html(
                kpi_card(
                    "Total Arrecadado Real",
                    fmt_compact(float(row["total_arrecadado"])),
                    sub="ano parcial" if year == ANO_ATUAL else (pct_delta(_total_serie) or ""),
                    accent=True,
                )
            )
        else:
            st.html(kpi_card("Total Arrecadado Real", "N/D"))

    if _tem_arrecadado:
        pct_progresso = float(row["pct_arrecadado"])
        _pct_int = min(int(pct_progresso * 100), 100)
        st.html(
            f'<div style="background:#fff;border:1px solid #e7e9ee;border-radius:14px;padding:20px 24px;margin-bottom:1.5rem">'
            f'<div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:9px">'
            f'<strong style="font-weight:600">Progresso de arrecadação anual</strong>'
            f"<strong style=\"font-family:'Source Serif 4',serif;font-weight:700\">{pct_progresso:.1%}</strong></div>"
            f'<div style="height:12px;background:#eef0f4;border-radius:7px;overflow:hidden">'
            f'<div style="width:{_pct_int}%;height:100%;background:linear-gradient(90deg,oklch(0.6 0.11 215),oklch(0.55 0.11 250));border-radius:7px"></div></div>'
            f"</div>"
        )

    # Tabela de detalhamento
    st.html(section_heading("Previsto vs. arrecadado por origem"))

    resumo_df = fontes_receita.tabela_detalhamento(row)

    if _tem_arrecadado:
        _max_val = float(resumo_df["Previsto"].max()) if not resumo_df.empty else 1.0
        _barra_rows = [
            (str(r["Fonte"]), float(r["Previsto"]), float(r["Arrecadado"]), _max_val) for _, r in resumo_df.iterrows()
        ]
        st.html(barra_comparativa(_barra_rows))

        st.dataframe(
            resumo_df.rename(columns={"Fonte": "Fonte ⓘ"}),
            column_config={
                "Fonte ⓘ": st.column_config.TextColumn(
                    help="Receita Própria: impostos e taxas municipais. Transferências da União: FPM, SUS, FUNDEB, etc. Transferências do Estado: ICMS, IPVA, etc."
                ),
                "Previsto": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Arrecadado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Diferença (Previsto − Arrecadado)": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Realização (%)": st.column_config.NumberColumn(format="%.2f%%"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        fig = px.pie(resumo_df, values="Previsto", names="Fonte")
        fig.update_layout(**plotly_card_layout("Distribuição da Previsão Orçamentária", height=320))
        st.html(plotly_card_start())
        st.plotly_chart(fig, use_container_width=True)
        st.html(plotly_card_end())

        st.dataframe(
            resumo_df[["Fonte", "Previsto"]],
            column_config={"Previsto": st.column_config.NumberColumn(format="R$ %,.2f")},
            use_container_width=True,
            hide_index=True,
        )

    if row["alerta_dependencia"]:
        st.html(
            alert_box(
                "<strong>Alta dependência fiscal.</strong> A receita própria representa menos de 10% do total — "
                "o município depende de repasses federais e estaduais para quase toda a sua arrecadação.",
                kind="warning",
            )
        )

st.caption(f"[Ver portal oficial de transparência →]({constants.PORTAL_URL})")
