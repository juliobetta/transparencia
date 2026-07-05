import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from shared import (
    CURRENT_YEAR,
    fmt_currency,
    get_conn,
    get_extraction_date,
    render_partial_year_notice,
    render_revenue_methodology,
    render_sidebar,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import fontes_receita, posicao_fiscal

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _receita(conn, year, _extracted_at):
    return fontes_receita.run(conn, [year])


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _posicao_fiscal(conn, year, _extracted_at, _v=6):
    return posicao_fiscal.run(conn, year)


conn = get_conn()
year = render_sidebar()
_extracted_at = get_extraction_date(conn)

st.header("Fontes de Receita")

# Aviso sobre limitações históricas dos dados
if year < CURRENT_YEAR:
    st.info(
        "O portal de transparência municipal disponibiliza previsões orçamentárias detalhadas para todos os anos, "
        f"mas os dados de arrecadação efetiva estão disponíveis na API apenas a partir do exercício de {CURRENT_YEAR}.",
        icon=":material/info:",
    )
else:
    st.success(
        f":material/check: Dados de Arrecadação Realizados disponíveis para o exercício corrente ({CURRENT_YEAR})."
    )
    render_partial_year_notice(year, _extracted_at)

render_revenue_methodology()

df = _receita(conn, year, _extracted_at)
if not df.empty:
    row = df.iloc[0]

    # Layout de duas colunas de métricas
    c1, c2 = st.columns(2)
    c1.metric(
        "Previsão Orçamentária",
        fmt_currency(row["total_previsto"]),
        help=(
            "Valor total de receitas que a prefeitura planejou arrecadar no ano, conforme aprovado na "
            "Lei Orçamentária Anual (LOA). É uma estimativa — o quanto efetivamente entra no caixa pode "
            "ser maior ou menor, dependendo do desempenho econômico e dos repasses federais e estaduais."
        ),
    )

    if year == CURRENT_YEAR:
        c2.metric(
            "Total Arrecadado Real",
            fmt_currency(row["total_arrecadado"]),
            help=(
                "Valor efetivamente recebido pela prefeitura no ano — ou seja, o dinheiro que de fato "
                "entrou no caixa municipal até a data da última atualização. Inclui impostos municipais "
                "pagos pelos cidadãos, transferências da União (como FPM e FUNDEB) e repasses do Estado "
                "(como ICMS e IPVA). Compare com a Previsão Orçamentária para saber se a arrecadação "
                "está dentro do esperado."
            ),
        )

        # Progress Bar
        pct_progresso = row["pct_arrecadado"]
        st.markdown(f"**Progresso de Arrecadação Anual: {pct_progresso * 100:.2f}%**")
        st.progress(min(max(pct_progresso, 0.0), 1.0))
    else:
        c2.metric("Total Arrecadado Real", "N/D (Não Disp. na API)")

    # Tabela de detalhamento
    st.subheader("Previsto vs. Arrecadado por Origem")

    resumo_df = fontes_receita.tabela_detalhamento(row, year)

    if year == CURRENT_YEAR:
        # Gráfico de barras: previsto vs. arrecadado
        df_comparativo = resumo_df.melt(
            id_vars=["Fonte"], value_vars=["Previsto", "Arrecadado"], var_name="Métrica", value_name="Valor"
        )
        fig = px.bar(
            df_comparativo,
            x="Fonte",
            y="Valor",
            color="Métrica",
            barmode="group",
            title="Comparação: Planejado (Previsão) vs. Arrecadado Real",
            labels={"Valor": "R$ (Reais)", "Fonte": "Fonte de Receita"},
        )
        fig.update_layout(yaxis_tickformat=",.2f")
        st.plotly_chart(fig, use_container_width=True)

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
        st.warning(
            ":material/warning: Alerta: Receita própria municipal está abaixo de 10% do total. Alta dependência fiscal de repasses federais e estaduais."
        )

if year == CURRENT_YEAR:
    st.divider()
    st.subheader(f"Situação Fiscal Estimada ({CURRENT_YEAR})")

    posicao_fiscal_data = _posicao_fiscal(conn, year, _extracted_at)

    ano_anterior = CURRENT_YEAR - 1
    st.warning(
        f"""
        **Estimativa baseada em dados públicos — não é um balanço oficial.**\n\n
        * **Fluxo Líquido do Período**: total arrecadado menos pagamentos efetivamente realizados no ano (orçamento corrente + restos pagos).
        Não representa o saldo de caixa disponível — não inclui saldo inicial em 01/01/{CURRENT_YEAR}, receitas/despesas extra-orçamentárias nem aplicações financeiras.
        * **Obrigações Herdadas**: restos a pagar de exercícios anteriores a {ano_anterior} (dívida da administração anterior) ainda não quitados. \n\n
        Para o valor oficial, consulte Prestação de Contas > Responsabilidade Fiscal - RREO no [portal da transparência]({glossary.PORTAL_URL}).
        """,
        icon=":material/warning:",
    )

    fc1, fc2, fc3 = st.columns(3)
    fc1.metric("Receitas Arrecadadas", fmt_currency(posicao_fiscal_data["total_arrecadado"]))
    fc2.metric(
        "Efetivamente Pago — Exercício Corrente",
        fmt_currency(posicao_fiscal_data["despesas_pagas"]),
        help=f"Despesas do orçamento de {CURRENT_YEAR} pagas no ano.",
    )
    fc3.metric(
        "Restos a Pagar Quitados",
        fmt_currency(posicao_fiscal_data["restos_pagos_no_ano"]),
        help=f"Pagamentos de empenhos de anos anteriores (Restos a Pagar) realizados em {CURRENT_YEAR}.",
    )

    fc3, fc4 = st.columns(2)
    fc3.metric("Fluxo Líquido do Período", fmt_currency(posicao_fiscal_data["saldo_estimado"]))
    herdadas = posicao_fiscal_data.get("restos_pendentes_anteriores", 0.0)
    fc4.metric(
        "Obrigações Herdadas (Adm. Anterior)",
        fmt_currency(herdadas),
        delta=f"-{fmt_currency(herdadas)}",
    )

    saldo_apos_restos = posicao_fiscal_data["saldo_apos_restos"]
    st.metric(
        f"Saldo após Restos Pendentes ({CURRENT_YEAR})",
        fmt_currency(saldo_apos_restos),
        delta=fmt_currency(saldo_apos_restos) if saldo_apos_restos >= 0 else f"-{fmt_currency(abs(saldo_apos_restos))}",
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
- Saldo inicial de caixa em 01/01/{CURRENT_YEAR}
- Receitas e despesas extra-orçamentárias
- Aplicações financeiras e disponibilidades bancárias

Para o valor oficial, consulte o **RREO Anexo 5** no portal de transparência.
            """
        )

    st.info("Detalhamento completo por fornecedor disponível em **Despesas → Restos a Pagar**.", icon=":material/info:")

st.caption(f"[Ver portal oficial de transparência →]({glossary.PORTAL_URL})")
