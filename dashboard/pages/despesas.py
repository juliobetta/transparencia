import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from shared import fmt_currency, fmt_currency_short, get_conn, get_extraction_date, render_sidebar
from sqlalchemy.engine import Engine

from analysis import expenses_analysis, fiscal_position, supplier_concentration
from analysis.expenses_analysis import get_searchable_diarias
from analysis.fiscal_position import unpaid_pie, unpaid_summary
from analysis.supplier_concentration import concentration_pie

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _metrics(conn, year, _extracted_at):
    return expenses_analysis.get_general_expense_metrics(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _by_unit(conn, year, _extracted_at):
    return expenses_analysis.get_expenses_by_unit(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _impact(conn, year, _extracted_at):
    return expenses_analysis.get_local_spending_impact(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _top_suppliers(conn, year, _extracted_at):
    return expenses_analysis.get_top_suppliers_detailed(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _concentration(conn, year, _extracted_at):
    return supplier_concentration.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _spending_by_city(conn, year, _extracted_at):
    return expenses_analysis.get_spending_by_city(conn, year, top_n=5)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _diarias_summary(conn, year, _extracted_at):
    return expenses_analysis.get_diarias_summary(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _top_diarias(conn, year, _extracted_at):
    return expenses_analysis.get_top_diarias_beneficiaries(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _unpaid_suppliers(conn, year, _extracted_at):
    return fiscal_position.get_unpaid_suppliers(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _low_value_restos(conn, _extracted_at):
    return fiscal_position.get_low_value_restos(conn)


conn = get_conn()
year = render_sidebar()
_extracted_at = get_extraction_date(conn)

st.title("Portal de Despesas Detalhadas")
st.caption("Detalhes sobre onde e como os recursos públicos estão sendo aplicados.")

# Tabs layout
t1, t2, t3, t4, t5 = st.tabs(
    [
        ":material/corporate_fare: Unidades Administrativas",
        ":material/handshake: Fornecedores e Compras Locais",
        ":material/hourglass: Restos a Pagar",
        ":material/flight_takeoff: Diárias e Viagens",
        ":material/manage_search: Consulta de Transações",
    ]
)

# Tab 1: Unidades Administrativas
with t1:
    st.subheader("Análise de Despesas por Unidade do Governo")

    metrics = _metrics(conn, year, _extracted_at)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Empenhado", fmt_currency(metrics["empenhado"]))
    c2.metric("Total Liquidado", fmt_currency(metrics["liquidado"]), f"Executado: {metrics['taxa_liquidacao']:.1f}%")
    c3.metric("Total Pago Real", fmt_currency(metrics["pago"]), f"Pago: {metrics['taxa_pagamento']:.1f}%")

    df_unit = _by_unit(conn, year, _extracted_at)
    if not df_unit.empty:
        st.markdown("---")
        fig = px.bar(
            df_unit.head(15),
            x="pago",
            y="descricao",
            orientation="h",
            title="Top 15 Unidades Administrativas por Valor Pago (R$)",
            labels={"pago": "Pago (R$)", "descricao": "Unidade Administrativa"},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df_unit.rename(
                columns={
                    "descricao": "Unidade Administrativa",
                    "empenhado": "Empenhado (R$)",
                    "liquidado": "Liquidado (R$)",
                    "pago": "Pago (R$)",
                    "dotacao_atualizada": "Dotação Atualizada (R$)",
                }
            ),
            column_config={
                "Empenhado (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Liquidado (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Pago (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Dotação Atualizada (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhuma despesa orçamentária registrada para este exercício.")

# Tab 2: Fornecedores
with t2:
    st.subheader("Concentração e Impacto Econômico de Fornecedores")
    st.caption(
        "Analisa para onde vai o dinheiro público: quanto fica na economia local, "
        "quanto vai para empresas de fora e se há concentração excessiva em poucos fornecedores. "
        "Compras locais acima de 30% e HHI abaixo de 2.500 são referências saudáveis. "
        'Pagamentos distribuídos via responsáveis de secretaria ("E OUTROS") são excluídos desta análise.'
    )

    impact = _impact(conn, year, _extracted_at)
    conc = _concentration(conn, year, _extracted_at)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Efetivamente Pago — Empresas Locais", fmt_currency_short(impact["local_pago"]))
    c2.metric("Efetivamente Pago — Empresas Externas", fmt_currency_short(impact["externo_pago"]))
    c3.metric(
        "Índice de Compras Locais",
        f"{impact['pct_local']:.2f}%",
        help="Percentual de recursos mantidos na economia local de Porciúncula.",
    )
    c4.metric(
        "HHI (concentração)",
        f"{conc['hhi']:,.0f}",
        help="Índice Herfindahl-Hirschman. Acima de 2.500 = concentração alta.",
    )

    if impact["total_pago"] > 0:
        pie_df = pd.DataFrame(
            {
                "Mercado": ["Negócios Locais (Porciúncula)", "Prestadores Externos"],
                "Pago (R$)": [impact["local_pago"], impact["externo_pago"]],
            }
        )
        fig_pie = px.pie(
            pie_df,
            values="Pago (R$)",
            names="Mercado",
            color="Mercado",
            color_discrete_map={"Negócios Locais (Porciúncula)": "#2b5c8f", "Prestadores Externos": "#a12c2c"},
            title="Destino Geográfico dos Recursos Públicos Pagos",
        )

        df_cities = _spending_by_city(conn, year, _extracted_at)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            if not df_cities.empty:
                fig_cities = px.pie(
                    df_cities,
                    values="pago",
                    names="cidade",
                    color="cidade",
                    color_discrete_map={"Negócios Locais (Porciúncula)": "#2b5c8f"},
                    title="Top 5 Cidades Externas + Outros",
                )
                st.plotly_chart(fig_cities, use_container_width=True)
    else:
        df_cities = _spending_by_city(conn, year, _extracted_at)
        if not df_cities.empty:
            fig_cities = px.pie(
                df_cities,
                values="pago",
                names="cidade",
                color="cidade",
                color_discrete_map={"Negócios Locais (Porciúncula)": "#2b5c8f"},
                title="Top 5 Cidades Externas + Outros",
            )
            st.plotly_chart(fig_cities, use_container_width=True)

    st.markdown("### Concentração de Fornecedores")
    if conc["dominante"]:
        st.warning(
            f"{conc['dominante']} recebeu mais de 40% do total empenhado a fornecedores.", icon=":material/warning:"
        )

    top10_conc = conc["top10"].copy()
    pie_conc = concentration_pie(top10_conc, conc["total_all"])
    fig_conc = px.pie(
        pie_conc, values="empenhado", names="Fornecedor", title="Distribuição do Empenhado — Top 10 Fornecedores"
    )
    st.plotly_chart(fig_conc, use_container_width=True)

    st.markdown("### Top 10 Maiores Prestadores de Serviços / Fornecedores")
    df_sup = _top_suppliers(conn, year, _extracted_at)
    if not df_sup.empty:
        fig_sup = px.bar(
            df_sup.head(10),
            x="pago",
            y="fornecedor",
            orientation="h",
            title="Top 10 Fornecedores por Valor Pago (R$)",
            labels={"pago": "Pago (R$)", "fornecedor": "Nome do Fornecedor"},
        )
        fig_sup.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_sup, use_container_width=True)

        st.dataframe(
            df_sup.rename(
                columns={"fornecedor": "Fornecedor", "insmf": "CNPJ/CPF", "cidade": "Cidade", "pago": "Total Pago (R$)"}
            )[["Fornecedor", "CNPJ/CPF", "Cidade", "Total Pago (R$)"]],
            column_config={"Total Pago (R$)": st.column_config.NumberColumn(format="R$ %,.2f")},
            use_container_width=True,
            hide_index=True,
        )

# Tab 3: Restos a Pagar
with t3:
    st.subheader("Fornecedores com Pagamento Pendente")

    unpaid_df = _unpaid_suppliers(conn, year, _extracted_at)
    if not unpaid_df.empty:
        rp = unpaid_summary(unpaid_df)

        rc1, rc2, rc3 = st.columns(3)
        rc1.metric("Total Pendente", fmt_currency(rp["total"]), help="Soma de todos os empenhos ainda não quitados.")
        rc2.metric("Fornecedores aguardando", rp["count"])
        rc3.metric("Dívida mais antiga desde", str(rp["oldest"]))

        pie_df = unpaid_pie(unpaid_df)
        fig_rp = px.pie(
            pie_df,
            values="Pendente",
            names="Fornecedor",
            title="Top 10 Fornecedores com Maior Pendência",
        )
        st.plotly_chart(fig_rp, use_container_width=True)

        st.dataframe(
            unpaid_df.rename(
                columns={
                    "descricao": "Fornecedor",
                    "aguardando_desde": "Aguardando desde",
                    "num_registros": "Nº registros",
                    "total_empenhado": "Total Empenhado",
                    "total_pago": "Total Pago",
                    "pendente": "Pendente",
                }
            )[["Fornecedor", "Aguardando desde", "Nº registros", "Total Empenhado", "Total Pago", "Pendente"]],
            column_config={
                "Total Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Total Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Pendente": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum fornecedor com pagamento pendente para este exercício.")

    low_value_df = _low_value_restos(conn, _extracted_at)
    if not low_value_df.empty:
        with st.expander(
            f":material/warning: {len(low_value_df)} registro(s) com empenhado abaixo de R$ 10,00 — verificar"
        ):
            st.warning(
                "Estes registros possuem valores empenhados muito baixos e podem indicar erros de lançamento ou dados inconsistentes na fonte."
            )
            st.dataframe(
                low_value_df,
                column_config={
                    "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
                },
                use_container_width=True,
                hide_index=True,
            )

# Tab 4: Diárias
with t4:
    st.subheader("Diárias e Auxílios de Viagem a Serviço")

    dia_sum = _diarias_summary(conn, year, _extracted_at)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pago em Diárias", fmt_currency(dia_sum["total_valor"]))
    c2.metric("Total de Servidores Beneficiários", int(dia_sum["total_viajantes"]))
    c3.metric("Média de Reembolso por Viagem", fmt_currency(dia_sum["media_reembolso"]))

    st.markdown("---")
    df_dia_top = _top_diarias(conn, year, _extracted_at)
    if not df_dia_top.empty:
        st.markdown("### Top 10 Servidores que Receberam Diárias")
        st.dataframe(
            df_dia_top.rename(
                columns={
                    "favorecido": "Servidor Público",
                    "cargo": "Cargo",
                    "valor": "Total Recebido (R$)",
                    "viagens": "Qtd Viagens",
                }
            ),
            column_config={"Total Recebido (R$)": st.column_config.NumberColumn(format="R$ %,.2f")},
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Histórico e Detalhes dos Pagamentos de Diárias")
        st.info("Insira o nome do servidor ou departamento abaixo para buscar viagens específicas.")

        search_dia = st.text_input("Buscar Diária (Nome do Servidor ou Unidade):", "")
        df_dia_list = get_searchable_diarias(conn, year, search_dia)
        if not df_dia_list.empty:
            st.dataframe(
                df_dia_list.rename(
                    columns={
                        "data": "Data",
                        "servidor": "Servidor",
                        "cargo": "Cargo/Função",
                        "valor": "Valor (R$)",
                        "unidade": "Unidade Administrativa",
                        "historico": "Justificativa da Viagem",
                    }
                ),
                column_config={"Valor (R$)": st.column_config.NumberColumn(format="R$ %,.2f")},
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("Nenhuma viagem correspondente encontrada.")
    else:
        st.info("Nenhum pagamento de diárias registrado para este exercício.")

# Tab 5: Consulta Geral de Transações
with t5:
    st.subheader("Pesquisa Geral de Transações Financeiras (Contábeis)")
    st.markdown(
        "Pesquise diretamente no livro caixa e no razão da prefeitura. "
        "Você pode buscar por nome de empresa, órgão ou termos específicos (ex: *asfalto*, *combustível*, *medicamento*)."
    )

    search_q = st.text_input("Termo de Busca:", placeholder="Digite para pesquisar...")
    limit_q = st.slider("Qtd. Máxima de Resultados:", min_value=50, max_value=1000, value=250, step=50)

    if search_q.strip() or year:
        df_t = expenses_analysis.get_searchable_transactions(conn, year, search_q, limit_q)
        if not df_t.empty:
            st.markdown(f"Exibindo os **{len(df_t)}** maiores pagamentos contábeis correspondentes:")
            st.dataframe(
                df_t.rename(
                    columns={
                        "data": "Data Empenho",
                        "fornecedor": "Fornecedor / Favorecido",
                        "pago": "Valor Pago (R$)",
                        "unidade": "Unidade",
                        "descricao": "Justificativa Contábil (Histórico)",
                    }
                ),
                column_config={
                    "Valor Pago (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Data Empenho": st.column_config.DateColumn(format="DD/MM/YYYY"),
                },
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("Nenhum pagamento correspondente encontrado para a busca.")
