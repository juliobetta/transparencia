import sys
from datetime import date
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
    comparison,
    contract_anomalies,
    payroll_vs_services,
    revenue_sources,
    supplier_concentration,
    yoy_trends,
)
from analysis.comparison import PeriodSpec

st.set_page_config(page_title="Transparência Porciúncula", layout="wide")

YEARS = list(range(2022, date.today().year + 1))


@st.cache_resource
def get_conn():
    return db.get_connection()


conn = get_conn()


def _comparison_table(domain: dict, rows: list[tuple[str, str]], fmt: str) -> pd.DataFrame:
    records = []
    for label, key in rows:
        d = domain[key]
        records.append(
            {
                "Métrica": label,
                "Período A": fmt.format(d["a"]),
                "Período B": fmt.format(d["b"]),
                "Δ Absoluto": ("+" if d["abs"] >= 0 else "") + fmt.format(d["abs"]),
                "Δ %": f"{d['pct']:+.1f}%" if d["pct"] is not None else "N/D",
            }
        )
    return pd.DataFrame(records)


def _fmt_delta(d: dict, fmt: str = "{:+,.0f}") -> str:
    if d["pct"] is None:
        return "N/D"
    return f"{fmt.format(d['abs'])} ({d['pct']:+.1f}%)"


# Persistent portal link in sidebar
st.sidebar.markdown(
    f"### 🔗 Portal Oficial\n[Ver fonte oficial →]({glossary.PORTAL_URL})",
    unsafe_allow_html=True,
)
year = st.sidebar.selectbox("Ano", YEARS, index=len(YEARS) - 2)

_last_extracted = db.get_metadata(conn, "last_extracted_at")
if _last_extracted:
    from datetime import datetime

    _last_extracted = datetime.strptime(_last_extracted, "%Y-%m-%d").strftime("%m/%d/%Y")
st.sidebar.markdown("---")
st.sidebar.caption(f"Última extração: **{_last_extracted}**" if _last_extracted else "Última extração: desconhecida")

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
        "Comparação",
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

    st.subheader("Tendências Ano a Ano")
    yoy = yoy_trends.run(conn, list(range(2022, year + 1)))
    st.dataframe(
        yoy.rename(
            columns={
                "ano": "Ano",
                "total_gasto": "Total Gasto (R$)",
                "total_folha": "Total Folha (R$)",
                "total_receita": "Total Receita (R$)",
                "restos_a_pagar": "Restos a Pagar (R$)",
                "total_gasto_pct_change": "Δ% Gasto",
                "total_folha_pct_change": "Δ% Folha",
                "total_receita_pct_change": "Δ% Receita",
                "restos_a_pagar_pct_change": "Δ% Restos",
            }
        ),
        use_container_width=True,
    )

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
    st.info(
        "Contratos sem processo licitatório são comuns e frequentemente legais — dispensas de baixo valor "
        "e inexigibilidades são permitidas por lei. O ponto de atenção são os contratos **acima de R$57k** "
        "sem licitação, pois nesses casos a lei exige justificativa formal."
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Acima do limite legal (R$57k)", len(acima))
    c2.metric("Acima do limite — Saúde", len(saude), help="Contratos acima de R$57k sem licitação em órgãos de saúde.")
    c3.metric("Total sem processo licitatório", len(gaps))
    acima_df = gaps[gaps["acima_limite"]]
    if not acima_df.empty:
        st.subheader("Contratos acima do limite legal sem licitação")
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
    st.info(
        "⚠️ O portal de transparência só disponibiliza dados de receita para o exercício corrente. "
        "Comparações históricas não estão disponíveis via API."
    )
    with st.expander("ℹ️ O que isso significa?"):
        st.write(f"**Receita Própria:** {glossary.tooltip('Receita Própria')}")
        st.write(f"**FPM:** {glossary.tooltip('FPM (Fundo de Participação dos Municípios)')}")
    df = revenue_sources.run(conn, list(range(2022, year + 1)))
    if not df.empty:
        row = df[df["ano"] == year]
        if not row.empty:
            row = row.iloc[0]
            values = [row["receita_propria"], row["transferencias_uniao"], row["transferencias_estado"]]
            if any(v > 0 for v in values):
                fig, ax = plt.subplots()
                ax.pie(
                    values,
                    labels=["Receita Própria", "Transferências União", "Transferências Estado"],
                    autopct="%1.1f%%",
                    startangle=90,
                )
                ax.set_title("Distribuição de Receitas (Previsão Atualizada)")
                st.pyplot(fig)
                st.caption("Fonte: previsão atualizada — dados de arrecadação efetiva não disponíveis na API.")
            else:
                st.info("Sem dados de receita para o ano selecionado.")
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

# ── Tab 6: Comparação ───────────────────────────────────────────────────────
with tabs[6]:
    st.header("Comparação de Períodos")
    st.caption("Compare dois períodos e veja as variações em cada dimensão.")

    MONTHS = list(range(1, 13))
    MONTH_NAMES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Período A")
        year_a = st.selectbox("Ano A", YEARS, index=0, key="cmp_year_a")
        m_start_a = st.selectbox(
            "Mês início A", MONTHS, index=0, format_func=lambda m: MONTH_NAMES[m - 1], key="cmp_ms_a"
        )
        m_end_a = st.selectbox("Mês fim A", MONTHS, index=11, format_func=lambda m: MONTH_NAMES[m - 1], key="cmp_me_a")
    with col_b:
        st.subheader("Período B")
        year_b = st.selectbox("Ano B", YEARS, index=len(YEARS) - 1, key="cmp_year_b")
        m_start_b = st.selectbox(
            "Mês início B", MONTHS, index=0, format_func=lambda m: MONTH_NAMES[m - 1], key="cmp_ms_b"
        )
        m_end_b = st.selectbox("Mês fim B", MONTHS, index=11, format_func=lambda m: MONTH_NAMES[m - 1], key="cmp_me_b")

    spec_a = PeriodSpec(year=year_a, month_start=m_start_a, month_end=m_end_a)
    spec_b = PeriodSpec(year=year_b, month_start=m_start_b, month_end=m_end_b)

    result = comparison.run(conn, spec_a, spec_b)

    st.subheader("Resumo")
    m1, m2, m3, m4 = st.columns(4)
    d = result["despesas"]["empenhado"]
    m1.metric("Empenhado (R$)", f"{d['b']:,.0f}", delta=_fmt_delta(d))
    d = result["pessoal"]["percentual_folha"]
    m2.metric("Folha / Gastos", f"{d['b']:.1f}%", delta=_fmt_delta(d, "{:+.1f}%"))
    d = result["licitacoes"]["sem_licitacao"]
    m3.metric("Sem Licitação", f"{d['b']:.0f}", delta=_fmt_delta(d, "{:+.0f}"))
    d = result["fornecedores"]["hhi"]
    m4.metric("HHI", f"{d['b']:,.0f}", delta=_fmt_delta(d))

    with st.expander("Despesas"):
        rows = [
            ("Empenhado (R$)", "empenhado"),
            ("Dotação Atualizada (R$)", "dotacao"),
        ]
        st.dataframe(
            _comparison_table(result["despesas"], rows, "{:,.0f}"),
            use_container_width=True,
        )

    with st.expander("Pessoal"):
        rows = [("Total Folha (R$)", "total_folha"), ("% dos Gastos", "percentual_folha")]
        st.dataframe(
            _comparison_table(result["pessoal"], rows, "{:.2f}"),
            use_container_width=True,
        )

    with st.expander("Licitações"):
        rows = [
            ("Contratos sem Licitação", "sem_licitacao"),
            ("Acima do Limite Legal", "acima_limite"),
            ("Na Saúde", "saude"),
        ]
        st.dataframe(
            _comparison_table(result["licitacoes"], rows, "{:.0f}"),
            use_container_width=True,
        )

    with st.expander("Fornecedores"):
        rows = [("HHI", "hhi")]
        st.dataframe(
            _comparison_table(result["fornecedores"], rows, "{:,.0f}"),
            use_container_width=True,
        )

    st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")

# ── Tab 7: Dados Brutos ─────────────────────────────────────────────────────
_COLUMN_LABELS = {
    "ano": "Ano",
    "empresa": "Entidade",
    "codigo": "Código",
    "descricao": "Descrição",
    "empenhado": "Empenhado (R$)",
    "liquidado": "Liquidado (R$)",
    "pago": "Pago (R$)",
    "dotac": "Dotação Inicial (R$)",
    "altdo": "Alterações (R$)",
    "dotacao_atualizada": "Dotação Atualizada (R$)",
    "numero": "Número",
    "modalidade": "Modalidade",
    "objeto": "Objeto",
    "valor": "Valor (R$)",
    "situacao": "Situação",
    "data_abertura": "Data de Abertura",
    "fornecedor": "Fornecedor",
    "data_inicio": "Data Início",
    "data_fim": "Data Fim",
    "licitacao_numero": "Nº Licitação",
    "mes": "Mês",
    "matricula": "Matrícula",
    "nome": "Nome",
    "cargo": "Cargo",
    "proventos": "Proventos (R$)",
    "descontos": "Descontos (R$)",
    "liquido_isnull_proventos_0_isnull_descontos_0": "Líquido (R$)",
    "previsto": "Previsto (R$)",
    "arrecadado": "Arrecadado (R$)",
    "previsao_inicial": "Previsão Inicial (R$)",
    "previsao_atualizada": "Previsão Atualizada (R$)",
    "arrecadado_periodo": "Arrecadado no Período (R$)",
    "arrecadado_total": "Arrecadado Total (R$)",
}

_TABLE_LABELS = {
    "despesas_por_orgao": "Despesas por Órgão",
    "despesas_por_fornecedor": "Despesas por Fornecedor",
    "licitacoes": "Licitações",
    "contratos": "Contratos",
    "pessoal": "Pessoal",
    "receita_orcamentaria": "Receita Orçamentária",
}

with tabs[7]:
    st.header("Dados Brutos")
    allowed_tables = list(_TABLE_LABELS.keys())
    table = st.selectbox("Tabela", allowed_tables, format_func=lambda t: _TABLE_LABELS[t])
    if table not in allowed_tables:
        raise ValueError(f"Tabela inválida: {table}")
    df = pd.read_sql_query(f"SELECT * FROM {table} WHERE ano = ?", conn, params=(year,))
    st.dataframe(df.fillna("N/D").rename(columns=_COLUMN_LABELS), use_container_width=True)
    st.download_button("Baixar CSV", df.to_csv(index=False).encode(), file_name=f"{table}_{year}.csv", mime="text/csv")
    st.caption(f"Fonte: [Portal de Transparência]({glossary.PORTAL_URL})")
