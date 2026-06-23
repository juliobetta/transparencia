import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import db
import glossary
from analysis import (
    bidding_gaps,
    budget_execution,
    contract_anomalies,
    payroll_vs_services,
    revenue_sources,
    supplier_concentration,
)

st.set_page_config(page_title="Transparência Porciúncula", layout="wide")

YEARS = list(range(2022, 2027))


@st.cache_resource
def get_conn():
    return db.get_connection()


conn = get_conn()

# Persistent portal link in sidebar
st.sidebar.markdown(
    f"### 🔗 Portal Oficial\n[Ver fonte oficial →]({glossary.PORTAL_URL})",
    unsafe_allow_html=True,
)
year = st.sidebar.selectbox("Ano", YEARS, index=len(YEARS) - 2)

st.title("Transparência Porciúncula / RJ")
st.caption(f"Dados extraídos do [Portal de Transparência]({glossary.PORTAL_URL}) do município.")

tabs = st.tabs(
    [
        "Visão Geral",
        "Execução Orçamentária",
        "Fornecedores",
        "Licitações e Contratos",
        "Receitas",
        "Pessoal",
        "Dados Brutos",
    ]
)

# ── Tab 0: Visão Geral ──────────────────────────────────────────────────────
with tabs[0]:
    st.header("Visão Geral")
    budget = budget_execution.run(conn, year)
    supplier = supplier_concentration.run(conn, year)
    bidding = bidding_gaps.run(conn, year)
    revenue = revenue_sources.run(conn, [year])
    payroll = payroll_vs_services.run(conn, [year])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total empenhado (R$)", f"{budget['empenhado'].sum():,.0f}", help=glossary.tooltip("Empenho"))
    c2.metric(
        "Contratos sem licitação",
        int((bidding["licitacao_numero"].fillna("").str.strip() == "").sum()),
        help=glossary.tooltip("Licitação"),
    )
    if not revenue.empty:
        c3.metric("Receita própria", f"{revenue.iloc[0]['pct_propria']:.1f}%", help=glossary.tooltip("Receita Própria"))
    if not payroll.empty:
        c4.metric("Folha / gastos totais", f"{payroll.iloc[0]['percentual_folha']:.1f}%")

    st.info(f"🔗 Para informações detalhadas, acesse o portal oficial: [{glossary.PORTAL_URL}]({glossary.PORTAL_URL})")

# ── Tab 1: Execução Orçamentária ────────────────────────────────────────────
with tabs[1]:
    st.header("Execução Orçamentária por Órgão")
    with st.expander("ℹ️ O que isso significa?"):
        st.write(f"**Dotação Atualizada:** {glossary.tooltip('Dotação Atualizada')}")
        st.write(f"**Empenho:** {glossary.tooltip('Empenho')}")
    df = budget_execution.run(conn, year)
    st.dataframe(
        df[["descricao", "empenhado", "dotacao_atualizada", "taxa_execucao", "alerta"]].rename(
            columns={
                "descricao": "Órgão",
                "empenhado": "Empenhado (R$)",
                "dotacao_atualizada": "Dotação (R$)",
                "taxa_execucao": "Taxa de Execução",
                "alerta": "Situação",
            }
        ),
        use_container_width=True,
    )
    st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")

# ── Tab 2: Fornecedores ─────────────────────────────────────────────────────
with tabs[2]:
    st.header("Concentração de Fornecedores")
    with st.expander("ℹ️ O que isso significa?"):
        st.write(f"**Fornecedor:** {glossary.tooltip('Fornecedor')}")
        st.write("**HHI:** Índice de concentração de mercado. Acima de 2.500 indica alta concentração.")
    result = supplier_concentration.run(conn, year)
    if result["dominante"]:
        st.warning(f"⚠️ {result['dominante']} recebeu mais de 40% do total pago a fornecedores.")
    st.metric(
        "HHI (concentração)",
        f"{result['hhi']:,.0f}",
        help="Índice Herfindahl-Hirschman. Acima de 2.500 = concentração alta.",
    )
    st.dataframe(
        result["top10"][["descricao", "empenhado", "percentual"]].rename(
            columns={"descricao": "Fornecedor", "empenhado": "Empenhado (R$)", "percentual": "%"}
        ),
        use_container_width=True,
    )
    st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")

# ── Tab 3: Licitações e Contratos ───────────────────────────────────────────
with tabs[3]:
    st.header("Licitações e Contratos")
    with st.expander("ℹ️ O que isso significa?"):
        st.write(f"**Licitação:** {glossary.tooltip('Licitação')}")
        st.write(f"**Dispensa:** {glossary.tooltip('Dispensa de Licitação')}")
    gaps = bidding_gaps.run(conn, year)
    anomalies = contract_anomalies.run(conn, year)
    acima = gaps[gaps["acima_limite"]]
    saude = gaps[gaps["acima_limite"] & gaps["orgao_saude"]]
    c1, c2, c3 = st.columns(3)
    c1.metric("Contratos sem licitação", len(gaps))
    c2.metric("Acima do limite legal (R$57k)", len(acima))
    c3.metric("Na Saúde (Empresa 2)", len(saude))
    acima_df = gaps[gaps["acima_limite"]]
    if not acima_df.empty:
        st.subheader("Contratos sem licitação acima do limite legal")
        st.dataframe(
            acima_df[["numero", "empresa", "fornecedor", "objeto", "valor", "orgao_saude"]].rename(
                columns={
                    "numero": "Nº",
                    "empresa": "Entidade",
                    "fornecedor": "Fornecedor",
                    "objeto": "Objeto",
                    "valor": "Valor (R$)",
                    "orgao_saude": "Saúde?",
                }
            ),
            use_container_width=True,
        )
    if not anomalies["splitting"].empty:
        st.subheader("⚠️ Possível fracionamento de contratos")
        st.dataframe(anomalies["splitting"][["fornecedor", "valor", "objeto"]], use_container_width=True)
    st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")

# ── Tab 4: Receitas ─────────────────────────────────────────────────────────
with tabs[4]:
    st.header("Fontes de Receita")
    with st.expander("ℹ️ O que isso significa?"):
        st.write(f"**Receita Própria:** {glossary.tooltip('Receita Própria')}")
        st.write(f"**FPM:** {glossary.tooltip('FPM (Fundo de Participação dos Municípios)')}")
    df = revenue_sources.run(conn, list(range(2022, year + 1)))
    if not df.empty:
        row = df[df["ano"] == year]
        if not row.empty:
            row = row.iloc[0]
            fig, ax = plt.subplots()
            ax.pie(
                [row["receita_propria"], row["transferencias_uniao"], row["transferencias_estado"]],
                labels=["Receita Própria", "Transferências União", "Transferências Estado"],
                autopct="%1.1f%%",
                startangle=90,
            )
            st.pyplot(fig)
            if row["alerta_dependencia"]:
                st.warning("⚠️ Receita própria abaixo de 10% — alta dependência de repasses federais/estaduais.")
    st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")

# ── Tab 5: Pessoal ──────────────────────────────────────────────────────────
with tabs[5]:
    st.header("Folha de Pagamento")
    with st.expander("ℹ️ O que isso significa?"):
        st.write("Percentual dos gastos pagos que corresponde à folha de pessoal (servidores municipais).")
    df = payroll_vs_services.run(conn, list(range(2022, year + 1)))
    if not df.empty:
        fig, ax = plt.subplots()
        ax.bar(df["ano"].astype(str), df["percentual_folha"], color="#2e86c1")
        ax.set_ylabel("% dos gastos")
        ax.set_title("Folha / Total de Gastos (%)")
        st.pyplot(fig)
    st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")

# ── Tab 6: Dados Brutos ─────────────────────────────────────────────────────
with tabs[6]:
    st.header("Dados Brutos")
    table = st.selectbox(
        "Tabela",
        [
            "despesas_por_orgao",
            "despesas_por_fornecedor",
            "licitacoes",
            "contratos",
            "pessoal",
            "receita_orcamentaria",
        ],
    )
    df = pd.read_sql_query(f"SELECT * FROM {table} WHERE ano = ?", conn, params=(year,))
    st.dataframe(df, use_container_width=True)
    st.download_button("Baixar CSV", df.to_csv(index=False).encode(), file_name=f"{table}_{year}.csv", mime="text/csv")
    st.caption(f"Fonte: [Portal de Transparência]({glossary.PORTAL_URL})")
