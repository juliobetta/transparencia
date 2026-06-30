import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import get_conn, get_extraction_date, render_sidebar
from sqlalchemy.engine import Engine

import glossary
from analysis import adesao_de_ata, bidding_gaps, contract_anomalies
from analysis.constants import THRESHOLD_COMPRAS_SERVICOS

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _gaps(conn, year, _extracted_at):
    return bidding_gaps.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao(conn, year, _extracted_at):
    return adesao_de_ata.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_externa(conn, year, _extracted_at):
    return adesao_de_ata.run_external(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _anomalies(conn, year, _extracted_at):
    return contract_anomalies.run(conn, year)


conn = get_conn()
year = render_sidebar()
_extracted_at = get_extraction_date(conn)

gaps = _gaps(conn, year, _extracted_at)
adesao = _adesao(conn, year, _extracted_at)
adesao_externa = _adesao_externa(conn, year, _extracted_at)
anomalies = _anomalies(conn, year, _extracted_at)

acima = bidding_gaps.filter_above_limit(gaps)
saude = bidding_gaps.filter_above_limit_health(gaps)

st.header("Licitações e Contratos")

_threshold_fmt = f"R$ {THRESHOLD_COMPRAS_SERVICOS:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
st.info(
    "Contratos sem processo licitatório são comuns e frequentemente legais — dispensas de baixo valor "
    f"e inexigibilidades são permitidas por lei. O ponto de atenção são os contratos **acima de {_threshold_fmt}** "
    "sem licitação, pois nesses casos a lei exige justificativa formal "
    "([Lei 14.133/21, Art. 75, I](https://licitacoesecontratos.tcu.gov.br/5-10-2-1-dispensa-em-razao-do-valor-incisos-i-e-ii-2/))."
)

st.subheader("Resumo")
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Acima do limite legal ({_threshold_fmt})", len(acima))
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
            column_config={
                "Valor Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
            },
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
            "Entidade": None,
        },
        width="stretch",
        hide_index=True,
    )
if not anomalies["splitting"].empty:
    st.subheader(":material/warning: Possível fracionamento de contratos")
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
