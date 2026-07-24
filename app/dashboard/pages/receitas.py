import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from shared import (
    ANO_ATUAL,
    ANO_INICIAL,
    COLOR_POSITIVE,
    SPARK_CFG,
    alert_box,
    barra_comparativa,
    fmt_compact,
    fmt_currency,
    get_conn,
    get_data_extracao,
    kpi_card,
    kpi_grid,
    page_header,
    partial_year_month,
    pct_delta,
    render_aviso_ano_parcial,
    render_metodologia_receita,
    render_sidebar,
    section_heading,
    sparkline,
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

render_metodologia_receita()

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
    _anos_hist = df_hist["ano"].tolist()
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
        st.plotly_chart(
            sparkline(_anos_hist, _prev_serie), use_container_width=True, config=SPARK_CFG, key="spark_rec_prev"
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
        st.plotly_chart(
            sparkline(_anos_hist, _total_serie, COLOR_POSITIVE),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_rec_total",
        )

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
        fig = px.pie(resumo_df, values="Previsto", names="Fonte", title="Distribuição da Previsão Orçamentária")
        st.plotly_chart(fig, use_container_width=True)

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

if year == ANO_ATUAL:
    st.html(section_heading(f"Situação Fiscal Estimada ({ANO_ATUAL})"))

    posicao_fiscal_data = _posicao_fiscal(conn, year, empresa_ids, _extracted_at)

    ano_anterior = ANO_ATUAL - 1
    st.warning(
        f"""
        **Estimativa baseada em dados públicos — não é um balanço oficial.**\n\n
        * **Fluxo Líquido do Período**: total arrecadado menos pagamentos efetivamente realizados no ano (orçamento corrente + restos pagos).
        Não representa o saldo de caixa disponível — não inclui saldo inicial em 01/01/{ANO_ATUAL}, receitas/despesas extra-orçamentárias nem aplicações financeiras.
        * **Obrigações Herdadas**: restos a pagar de exercícios anteriores a {ano_anterior} (dívida da administração anterior) ainda não quitados. \n\n
        Para o valor oficial, consulte Prestação de Contas > Responsabilidade Fiscal - RREO no [portal da transparência]({constants.PORTAL_URL}).
        """,
        icon=":material/warning:",
    )

    herdadas = posicao_fiscal_data.get("restos_pendentes_anteriores", 0.0)
    saldo_apos_restos = posicao_fiscal_data["saldo_apos_restos"]
    st.html(
        kpi_grid(
            kpi_card("Receitas Arrecadadas", fmt_compact(posicao_fiscal_data["total_arrecadado"])),
            kpi_card("Efetivamente Pago — Exercício Corrente", fmt_compact(posicao_fiscal_data["despesas_pagas"])),
            kpi_card("Restos a Pagar Quitados", fmt_compact(posicao_fiscal_data["restos_pagos_no_ano"])),
            cols=3,
        )
    )
    st.html(
        kpi_grid(
            kpi_card("Fluxo Líquido do Período", fmt_compact(posicao_fiscal_data["saldo_estimado"]), accent=True),
            kpi_card("Obrigações Herdadas (Adm. Anterior)", fmt_compact(herdadas), risk=True),
            kpi_card(
                f"Saldo após Restos Pendentes ({ANO_ATUAL})",
                fmt_compact(abs(saldo_apos_restos)),
                sub="positivo" if saldo_apos_restos >= 0 else "negativo",
                accent=saldo_apos_restos >= 0,
                risk=saldo_apos_restos < 0,
            ),
            cols=3,
        )
    )

    with st.expander(":material/table_chart: Restos a Pagar pendentes por exercício"):
        if posicao_fiscal_data["restos_pendentes"]:
            restos_df = pd.DataFrame(posicao_fiscal_data["restos_pendentes"]).rename(
                columns={
                    "ano": "Exercício",
                    "administracao": "Administração",
                    "empenhado": "Empenhado",
                    "pago": "Pago",
                    "pendente": "Pendente",
                }
            )
            st.dataframe(
                restos_df,
                column_config={
                    "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Pendente": st.column_config.NumberColumn(format="R$ %,.2f"),
                },
                use_container_width=True,
                hide_index=True,
            )
            st.metric(
                "Total Pendente (todos os exercícios)", fmt_currency(posicao_fiscal_data["restos_pendentes_total"])
            )
        else:
            st.info("Sem dados de Restos a Pagar disponíveis.")

        st.markdown(
            f"""
**Legenda da tabela:**
- **Adm. Anterior** (exercícios < {ano_anterior}) — obrigações deixadas pela administração anterior, refletidas em "Obrigações Herdadas" acima
- **Adm. Atual** (exercícios ≥ {ano_anterior}) — obrigações da administração corrente em processamento normal

**Não incluído no Fluxo Líquido:**
- Saldo inicial de caixa em 01/01/{ANO_ATUAL}
- Receitas e despesas extra-orçamentárias
- Aplicações financeiras e disponibilidades bancárias

Para o valor oficial, consulte o **RREO Anexo 5** no portal de transparência.
            """
        )

    st.info("Detalhamento completo por fornecedor disponível em **Despesas → Restos a Pagar**.", icon=":material/info:")

st.caption(f"[Ver portal oficial de transparência →]({constants.PORTAL_URL})")
