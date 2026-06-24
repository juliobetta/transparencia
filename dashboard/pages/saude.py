import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import get_conn, render_sidebar

import glossary
from analysis import health_story

conn = get_conn()
year = render_sidebar()

st.title("Fundo Municipal de Saúde")
st.caption(f"Dados do Fundo Municipal de Saúde extraídos do [Portal de Transparência]({glossary.PORTAL_URL}).")

data = health_story.run(conn, year)

# ── Seção 1: O que entrou ───────────────────────────────────────────────────
st.header("① O que entrou")
st.subheader("Emendas Parlamentares")
if data["emendas_total"] > 0:
    st.metric("Total de emendas (valor autorizado)", f"R$ {data['emendas_total']:,.0f}")
    if not data["emendas"].empty and data["emendas"].notna().any().any():
        st.dataframe(
            data["emendas"].rename(
                columns={
                    "numero": "Nº",
                    "descricao": "Objeto",
                    "valor": "Valor Autorizado (R$)",
                    "empenhado": "Empenhado (R$)",
                    "autor": "Autor",
                    "Tipo da Emenda": "Tipo da Emenda",
                    "Esfera de Origem": "Esfera de Origem",
                    "ato_normativo": "Ato Normativo",
                    "Destinação": "Destinação",
                }
            ),
            use_container_width=True,
            column_config={
                "Valor Autorizado (R$)": st.column_config.NumberColumn(format="%.2f"),
                "Empenhado (R$)": st.column_config.NumberColumn(format="%.2f"),
                "Nº": None,
                "Tipo da Emenda": None,
                "Esfera de Origem": None,
                "Destinação": None,
            },
            hide_index=True,
        )
    with st.expander("ℹ️ O que é uma emenda parlamentar?"):
        st.write(glossary.tooltip("Emenda Impositiva"))
else:
    st.info("Sem emendas parlamentares registradas para este ano.")

st.subheader("Orçamento")
budget = data["budget"]
c1, c2, c3 = st.columns(3)
c1.metric("Dotação Atualizada (R$)", f"{budget['dotacao']:,.0f}", help=glossary.tooltip("Dotação Atualizada"))
c2.metric("Total Empenhado (R$)", f"{budget['empenhado']:,.0f}", help=glossary.tooltip("Empenho"))
c3.metric("Taxa de Execução", f"{budget['taxa_execucao']:.1%}")
if budget["flag_under_execution"]:
    st.warning(f"⚠️ Taxa de execução abaixo de 70% ao final do ano {year}.")

st.subheader("Repasses da Prefeitura")
transfers_total = data["transfers_to_health_total"]
if transfers_total > 0:
    st.metric(
        "Total de repasses recebidos (R$)",
        f"{transfers_total:,.0f}",
        help="Valores transferidos pela Prefeitura Municipal ao Fundo de Saúde no ano.",
    )
else:
    st.info("Sem repasses registrados para este ano.")

# ── Seção 2: O que foi gasto ────────────────────────────────────────────────
st.header("② O que foi gasto")
st.subheader("Evolução do Gasto (Empenhado por Ano)")
trend = data["execution_trend"]
if not trend.empty:
    fig = px.bar(
        trend,
        x="ano",
        y="empenhado",
        title="Fundo de Saúde — Empenhado por Ano",
        labels={"ano": "Ano", "empenhado": "Empenhado (R$)"},
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        trend.rename(columns={"ano": "Ano", "empenhado": "Empenhado (R$)"}),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ano": st.column_config.NumberColumn(format="%d"),
            "Empenhado (R$)": st.column_config.NumberColumn(format="R$ %,.0f"),
        },
    )


# ── Seção 3: Como foi contratado ────────────────────────────────────────────
st.header("③ Como foi contratado")

c1, c2, c3 = st.columns(3)
c1.metric(
    "Licitações via Adesão de Ata (Carona)",
    data["adesao_de_ata_count"],
    help=glossary.tooltip("Adesão de Ata (Carona)"),
)
c2.metric("Qtd. de Contratos Vinculados", int(data["adesao_de_ata_list"]["has_contract"].sum()))
c3.metric("Valor Total Contratado via Adesão (R$)", f"{data['adesao_de_ata_value']:,.0f}")

if not data["adesao_de_ata_list"].empty:
    with st.expander("Ver licitações via Adesão de Ata"):
        st.dataframe(
            data["adesao_de_ata_list"].rename(
                columns={
                    "numero": "Nº Licit.",
                    "objeto": "Objeto",
                    "licitacao_valor": "Valor Est. Licitação (R$)",
                    "total_c_valor": "Valor Total Contratado (R$)",
                    "total_c_empenhado": "Valor Empenhado (R$)",
                    "has_contract": "Contrato Associado",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

st.subheader("Distribuição por Modalidade")
modality_df = data["contracts_by_modality"]
if not modality_df.empty and modality_df.notna().all().all():
    st.dataframe(
        modality_df.rename(columns={"modality": "Modalidade", "count": "Qtd", "total_value": "Valor Total (R$)"}),
        use_container_width=True,
        column_config={"Valor Total (R$)": st.column_config.NumberColumn(format="%.2f")},
        hide_index=True,
    )
    with st.expander("ℹ️ O que são essas modalidades?"):
        st.write(f"**Licitação:** {glossary.tooltip('Licitação')}")
        st.write(f"**Pregão Eletrônico:** {glossary.tooltip('Pregão Eletrônico')}")
        st.write(f"**Pregão Presencial:** {glossary.tooltip('Pregão Presencial')}")
        st.write(f"**Dispensa:** {glossary.tooltip('Dispensa de Licitação')}")
        st.write(f"**Inexigibilidade:** {glossary.tooltip('Inexigibilidade')}")
        st.write(f"**Adesão de Ata:** {glossary.tooltip('Adesão de Ata (Carona)')}")

st.subheader("Contratos sem Licitação acima de R$57k")
gaps = data["bidding_gaps"]
if not gaps.empty and gaps.notna().all().all():
    st.metric("Total de contratos", len(gaps))
    st.dataframe(
        gaps.rename(
            columns={
                "numero": "Nº",
                "fornecedor": "Fornecedor",
                "objeto": "Objeto",
                "valcon": "Valor (R$)",
                "modali": "Modalidade",
            }
        ),
        use_container_width=True,
        column_config={"Nº": None},
        hide_index=True,
    )
else:
    st.success("Nenhum contrato acima do limite legal sem processo licitatório.")

if not data["splitting"].empty and data["splitting"].notna().all().all():
    st.subheader("⚠️ Possível fracionamento de contratos")
    st.dataframe(data["splitting"][["fornecedor", "valcon", "objeto"]], use_container_width=True, hide_index=True)

# ── Seção 4: Quem recebeu ────────────────────────────────────────────────────
st.header("④ Quem recebeu")
st.metric(
    "HHI (concentração de fornecedores)",
    f"{data['hhi']:,.0f}",
    help="Índice Herfindahl-Hirschman. Acima de 2.500 = concentração alta.",
)
if not data["top_suppliers"].empty and data["top_suppliers"].notna().all().all():
    st.subheader("Top 10 Fornecedores")
    st.dataframe(
        data["top_suppliers"].rename(
            columns={"descricao": "Fornecedor", "empenhado": "Empenhado (R$)", "percentual": "%"}
        ),
        use_container_width=True,
        column_config={"codigo": None},
        hide_index=True,
    )

st.divider()
st.caption(f"Fonte: [Portal de Transparência]({glossary.PORTAL_URL})")

# ── Exportar relatório ───────────────────────────────────────────────────────
st.subheader("Exportar")

if "saude_report_year" not in st.session_state:
    st.session_state["saude_report_year"] = None

if st.button("Gerar Relatório HTML"):
    from report.saude import generate

    path = generate(conn, year)
    st.session_state["saude_report_year"] = (year, str(path))

if st.session_state["saude_report_year"] is not None:
    _year, _path = st.session_state["saude_report_year"]
    with open(_path, "rb") as f:
        st.download_button(
            label=f"Baixar relatório {_year} (HTML)",
            data=f,
            file_name=f"saude-{_year}.html",
            mime="text/html",
            key="download_saude_report",
        )
