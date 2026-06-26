import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from shared import fmt_currency, get_conn, render_sidebar
from sqlalchemy import text

from analysis import expenses_analysis

conn = get_conn()
year = render_sidebar()

st.title("Portal de Despesas Detalhadas")
st.caption("Acompanhe em tempo real como e onde os recursos públicos estão sendo aplicados.")

# Tabs layout
t1, t2, t3, t4 = st.tabs(
    [
        "🏢 Unidades Administrativas",
        "🤝 Fornecedores e Compras Locais",
        "✈️ Diárias e Viagens",
        "🔍 Consulta de Transações",
    ]
)

# Tab 1: Unidades Administrativas
with t1:
    st.subheader("Análise de Gastos por Unidade do Governo")

    metrics = expenses_analysis.get_general_expense_metrics(conn, year)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Empenhado", fmt_currency(metrics["empenhado"]))
    c2.metric("Total Liquidado", fmt_currency(metrics["liquidado"]), f"Executado: {metrics['taxa_liquidacao']:.1f}%")
    c3.metric("Total Pago Real", fmt_currency(metrics["pago"]), f"Pago: {metrics['taxa_pagamento']:.1f}%")

    df_unit = expenses_analysis.get_expenses_by_unit(conn, year)
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

    impact = expenses_analysis.get_local_spending_impact(conn, year)

    c1, c2, c3 = st.columns(3)
    c1.metric("Gasto com Empresas Locais", fmt_currency(impact["local_pago"]))
    c2.metric("Gasto com Empresas Externas", fmt_currency(impact["externo_pago"]))
    c3.metric(
        "Índice de Compras Locais",
        f"{impact['pct_local']:.2f}%",
        help="Percentual de recursos mantidos na economia local de Porciúncula.",
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
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("### Top 10 Maiores Prestadores de Serviços / Fornecedores")
    df_sup = expenses_analysis.get_top_suppliers_detailed(conn, year)
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

# Tab 3: Diárias
with t3:
    st.subheader("Diárias e Auxílios de Viagem a Serviço")

    dia_sum = expenses_analysis.get_diarias_summary(conn, year)

    c1, c2, c3 = st.columns(3)
    c1.metric("Gasto Total com Diárias", fmt_currency(dia_sum["total_valor"]))
    c2.metric("Total de Servidores Beneficiários", int(dia_sum["total_viajantes"]))
    c3.metric("Média de Reembolso por Viagem", fmt_currency(dia_sum["media_reembolso"]))

    st.markdown("---")
    df_dia_top = expenses_analysis.get_top_diarias_beneficiaries(conn, year)
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
        # Run dynamic query on SQL database for diarias
        if search_dia.strip():
            dia_sql = text("""
                SELECT data, favorecido as servidor, cargo, valor, unidade, descricao as historico
                FROM diarias
                WHERE ano = :ano AND (favorecido LIKE :search OR unidade LIKE :search OR cargo LIKE :search)
                ORDER BY data DESC
            """)
            dia_params = {"ano": year, "search": f"%{search_dia}%"}
        else:
            dia_sql = text("""
                SELECT data, favorecido as servidor, cargo, valor, unidade, descricao as historico
                FROM diarias
                WHERE ano = :ano
                ORDER BY data DESC LIMIT 150
            """)
            dia_params = {"ano": year}

        df_dia_list = pd.read_sql_query(dia_sql, conn, params=dia_params)
        if not df_dia_list.empty:
            df_dia_list["valor"] = pd.to_numeric(df_dia_list["valor"].str.replace(",", "."), errors="coerce").fillna(0)
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

# Tab 4: Consulta Geral de Transações
with t4:
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
                column_config={"Valor Pago (R$)": st.column_config.NumberColumn(format="R$ %,.2f")},
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("Nenhum pagamento correspondente encontrado para a busca.")
