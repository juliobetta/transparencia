import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import get_conn, render_sidebar

import glossary
from analysis import health_story

conn = get_conn()
year = render_sidebar()

st.header("Narrativa: Saúde")
st.caption("Análise focada na Secretaria Municipal de Saúde (empresa 2).")

data = health_story.run(conn, year)
budget = data["budget"]

c1, c2, c3 = st.columns(3)
c1.metric("Dotação (R$)", f"{budget['dotacao']:,.0f}")
c2.metric("Empenhado (R$)", f"{budget['empenhado']:,.0f}")
c3.metric("Taxa de Execução", f"{budget['taxa_execucao']:.1%}")

if budget["flag_under_execution"]:
    st.warning("⚠️ Taxa de execução orçamentária abaixo de 70% — possível subexecução.")

st.subheader("Tendência de Execução")
trend = data["execution_trend"]
if not trend.empty:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.bar(trend["ano"].astype(str), trend["empenhado"], color="#1a7f4b")
    ax.set_ylabel("Empenhado (R$)")
    ax.set_title("Execução Orçamentária — Saúde")
    st.pyplot(fig)

if data["emendas_total"] > 0:
    st.subheader("Emendas Parlamentares")
    st.metric("Total de Emendas (R$)", f"{data['emendas_total']:,.0f}")
    st.dataframe(data["emendas"], use_container_width=True)

st.subheader("Contratos por Modalidade")
if not data["contracts_by_modality"].empty:
    st.dataframe(data["contracts_by_modality"], use_container_width=True)

if data["adesao_de_ata_count"] > 0:
    st.subheader("Adesão de Ata (Carona)")
    st.metric("Contratos via carona", data["adesao_de_ata_count"])
    st.metric("Valor total caronas (R$)", f"{data['adesao_de_ata_value']:,.0f}")

st.subheader("Fornecedores — Top 10")
st.metric(
    "HHI (concentração)", f"{data['hhi']:,.0f}", help="Índice Herfindahl-Hirschman. Acima de 2.500 = concentração alta."
)
if not data["top_suppliers"].empty:
    st.dataframe(
        data["top_suppliers"][["descricao", "empenhado", "percentual"]].rename(
            columns={"descricao": "Fornecedor", "empenhado": "Empenhado (R$)", "percentual": "%"}
        ),
        use_container_width=True,
    )

if not data["bidding_gaps"].empty:
    st.subheader("⚠️ Contratos acima do limite legal sem licitação")
    st.dataframe(data["bidding_gaps"], use_container_width=True)

if not data["splitting"].empty:
    st.subheader("⚠️ Possível fracionamento de contratos")
    st.dataframe(data["splitting"][["fornecedor", "valor", "objeto"]], use_container_width=True)

st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
