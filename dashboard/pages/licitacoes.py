import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import get_conn, render_sidebar

import glossary
from analysis import adesao_de_ata, bidding_gaps, contract_anomalies

conn = get_conn()
year = render_sidebar()

st.header("Licitações e Contratos")
with st.expander("ℹ️ O que isso significa?"):
    st.write(f"**Licitação:** {glossary.tooltip('Licitação')}")
    st.write(f"**Dispensa:** {glossary.tooltip('Dispensa de Licitação')}")
gaps = bidding_gaps.run(conn, year)
adesao = adesao_de_ata.run(conn, year, "2")  # Using default health ID for now, need to be generic?
anomalies = contract_anomalies.run(conn, year)
acima = gaps[gaps["acima_limite"]]
saude = gaps[gaps["acima_limite"] & gaps["orgao_saude"]]

st.info(
    "Contratos sem processo licitatório são comuns e frequentemente legais — dispensas de baixo valor "
    "e inexigibilidades são permitidas por lei. O ponto de atenção são os contratos **acima de R$57k** "
    "sem licitação, pois nesses casos a lei exige justificativa formal."
)

st.subheader("Resumo")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Acima do limite legal (R$57k)", len(acima))
c2.metric("Acima do limite — Saúde", len(saude), help="Contratos acima de R$57k sem licitação em órgãos de saúde.")
c3.metric("Total sem processo licitatório", len(gaps))
c4.metric("Adesões de Ata", adesao["count"])

if not acima.empty:
    st.subheader("Contratos acima do limite legal sem licitação")
    st.dataframe(
        acima[["numero", "empresa", "fornecedor", "objeto", "valor", "orgao_saude"]].rename(
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
        hide_index=True,
    )
if not anomalies["splitting"].empty:
    st.subheader("⚠️ Possível fracionamento de contratos")
    st.dataframe(anomalies["splitting"][["fornecedor", "valor", "objeto"]], use_container_width=True, hide_index=True)
st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
