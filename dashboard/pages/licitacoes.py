import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
from shared import get_conn, render_sidebar

import glossary
from analysis import adesao_de_ata, bidding_gaps, contract_anomalies

conn = get_conn()
year = render_sidebar()

# ... rest of file, wrap analysis runs:
gaps = bidding_gaps.run(conn, year)
adesao = adesao_de_ata.run(conn, year, "2")
adesao_externa = adesao_de_ata.run_external(conn, year)
anomalies = contract_anomalies.run(conn, year)

# Create MM/YYYY column
for df in [gaps, adesao["list"], anomalies["splitting"]]:
    if isinstance(df, pd.DataFrame):
        if "mes" in df.columns and "ano" in df.columns:
            df["Período"] = df["mes"].astype(str).str.zfill(2) + "/" + df["ano"].astype(str)
        elif "mes" in df.columns:
            # Maybe ano is not in df but it should be available
            # If not, let's just use mes
            df["Período"] = df["mes"].astype(str).str.zfill(2)
        else:
            df["Período"] = ""

# Re-filter above (acima)
acima = gaps[gaps["acima_limite"]]
saude = gaps[gaps["acima_limite"] & gaps["orgao_saude"]]

st.header("Licitações e Contratos")

st.info(
    "Contratos sem processo licitatório são comuns e frequentemente legais — dispensas de baixo valor "
    "e inexigibilidades são permitidas por lei. O ponto de atenção são os contratos **acima de R$ 62.725,59** "
    "sem licitação, pois nesses casos a lei exige justificativa formal "
    "([Lei 14.133/21, Art. 75, I](https://licitacoesecontratos.tcu.gov.br/5-10-2-1-dispensa-em-razao-do-valor-incisos-i-e-ii-2/))."
)

st.subheader("Resumo")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Acima do limite legal (R$ 62.725,59)", len(acima))
c2.metric("Total sem processo licitatório", len(gaps))
c3.metric("Adesões de Ata (licitações)", adesao["count"])
c4.metric("Empenhos via Ata Externa", adesao_externa["count"])

# Fix gap table
gaps_display = gaps.rename(
    columns={
        "fornecedor": "Fornecedor",
        "objeto": "Objeto",
        "valcon": "Valor",
    }
)

with st.expander("Ver contratos sem processo licitatório"):
    # Drop 'numero' (Nº)
    cols_to_show = ["Fornecedor", "Objeto", "Valor", "Período"]
    df_to_show = gaps_display.drop(columns=["numero"], errors="ignore")
    st.dataframe(
        df_to_show[cols_to_show],
        column_config={
            "Valor": st.column_config.NumberColumn(format="R$ %,.2f"),
        },
        width="stretch",
        hide_index=True,
    )

with st.expander("Ver licitações via Adesão de Ata"):
    if not adesao["list"].empty:
        df_adesao = (
            adesao["list"]
            .rename(
                columns={
                    "objeto": "Objeto",
                    "periodo": "Período",
                    "licitacao_valor": "Valor Est. Licitação",
                    "total_c_valor": "Valor Total Contratado",
                    "total_c_empenhado": "Valor Empenhado",
                    "has_contract": "Contrato Associado",
                }
            )
            .drop(columns=["numero"], errors="ignore")
        )

        st.dataframe(
            df_adesao[
                [
                    "Objeto",
                    "Período",
                    "Valor Est. Licitação",
                    "Valor Total Contratado",
                    "Valor Empenhado",
                    "Contrato Associado",
                ]
            ],
            column_config={
                "Valor Est. Licitação": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Valor Total Contratado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Valor Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Nenhuma adesão de ata registrada para este ano.")

with st.expander("Ver empenhos via Ata de Registro de Preços Externa"):
    if not adesao_externa["list"].empty:
        st.caption(
            "Empenhos cuja justificativa contábil referencia uma Ata de Registro de Preços de outro ente "
            "(Termo de Adesão Externa). Esses registros complementam as licitações formais via carona."
        )
        st.dataframe(
            adesao_externa["list"].rename(
                columns={
                    "data": "Data",
                    "fornecedor": "Fornecedor",
                    "pago": "Valor Pago",
                    "unidade": "Unidade",
                    "justificativa": "Justificativa Contábil",
                    "num_licitacao": "Nº Licitação",
                }
            ),
            column_config={"Valor Pago": st.column_config.NumberColumn(format="R$ %,.2f")},
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Nenhum empenho com referência a ata externa registrado para este ano.")

if not acima.empty:
    st.subheader("Contratos acima do limite legal sem licitação")
    st.dataframe(
        acima[["empresa", "fornecedor", "objeto", "valcon", "orgao_saude", "Período"]].rename(
            columns={
                "empresa": "Entidade",
                "fornecedor": "Fornecedor",
                "objeto": "Objeto",
                "valcon": "Valor",
                "orgao_saude": "Saúde?",
            }
        ),
        column_config={
            "Valor": st.column_config.NumberColumn(format="R$ %,.2f"),
        },
        width="stretch",
        hide_index=True,
    )
if not anomalies["splitting"].empty:
    st.subheader("⚠️ Possível fracionamento de contratos")
    st.dataframe(
        anomalies["splitting"][["fornecedor", "valcon", "objeto", "Período"]].rename(
            columns={
                "fornecedor": "Fornecedor",
                "valcon": "Valor",
                "objeto": "Objeto",
            }
        ),
        column_config={
            "Valor": st.column_config.NumberColumn(format="R$ %,.2f"),
        },
        width="stretch",
        hide_index=True,
    )
st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
