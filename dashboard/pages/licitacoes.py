import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from shared import (
    ANO_ATUAL,
    ANO_INICIAL,
    SPARK_CFG,
    get_conn,
    get_data_extracao,
    pct_delta,
    render_aviso_ano_parcial,
    render_sidebar,
    sparkline,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import adesao_de_ata, anomalias_contratuais, licitacao_gaps
from analysis.constants import THRESHOLD_COMPRAS_SERVICOS

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _lacunas_licitacao(conn, year, _extracted_at):
    return licitacao_gaps.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao(conn, year, _extracted_at):
    return adesao_de_ata.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_externa(conn, year, _extracted_at):
    return adesao_de_ata.run_external(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _anomalias(conn, year, _extracted_at):
    return anomalias_contratuais.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _acima_por_ano(conn, years, _extracted_at):
    return licitacao_gaps.counts_by_year(conn, list(years))


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _totals_sem_lic_por_ano(conn, years, _extracted_at):
    return licitacao_gaps.totals_sem_licitacao_por_ano(conn, list(years))


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_por_ano(conn, years, _extracted_at):
    return adesao_de_ata.formal_counts_by_year(conn, list(years))


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_ext_por_ano(conn, years, _extracted_at):
    return adesao_de_ata.external_counts_by_year(conn, list(years))


conn = get_conn()
year = render_sidebar()
_extracted_at = get_data_extracao(conn)

lacunas = _lacunas_licitacao(conn, year, _extracted_at)
adesao = _adesao(conn, year, _extracted_at)
adesao_externa = _adesao_externa(conn, year, _extracted_at)
anomalias = _anomalias(conn, year, _extracted_at)

acima = licitacao_gaps.filter_above_limit(lacunas)
saude = licitacao_gaps.filter_above_limit_health(lacunas)

_all_years = list(range(ANO_INICIAL, year + 1))
_anos = _all_years
_hist_acima = _acima_por_ano(conn, tuple(_all_years), _extracted_at)
_hist_totals = _totals_sem_lic_por_ano(conn, tuple(_all_years), _extracted_at)
_hist_adesao = _adesao_por_ano(conn, tuple(_all_years), _extracted_at)
_hist_adesao_ext = _adesao_ext_por_ano(conn, tuple(_all_years), _extracted_at)

_acima_serie = [_hist_acima[y] for y in _anos]
_totals_serie = [_hist_totals[y] for y in _anos]
_adesao_serie = [_hist_adesao[y] for y in _anos]
_adesao_ext_serie = [_hist_adesao_ext[y] for y in _anos]

st.header("Licitações e Contratos")

if year == ANO_ATUAL:
    render_aviso_ano_parcial(year, _extracted_at)

_limite_fmt = f"R$ {THRESHOLD_COMPRAS_SERVICOS:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
st.info(
    "Contratos sem processo licitatório são comuns e frequentemente legais — dispensas de baixo valor "
    f"e inexigibilidades são permitidas por lei. O ponto de atenção são os contratos **acima de {_limite_fmt}** "
    "sem licitação, pois nesses casos a lei exige justificativa formal "
    "([Lei 14.133/21, Art. 75, I](https://licitacoesecontratos.tcu.gov.br/5-10-2-1-dispensa-em-razao-do-valor-incisos-i-e-ii-2/))."
)

st.subheader("Resumo")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(
        f"Acima do limite legal ({_limite_fmt})",
        len(acima),
        delta=pct_delta(_acima_serie),
        delta_color="inverse",
        help=(
            f"Número de contratos firmados sem licitação cujo valor ultrapassa {_limite_fmt} — "
            "o teto legal para dispensa em compras e serviços gerais (Decreto nº 12.807/2025). "
            "Acima desse valor, a lei exige processo licitatório formal com publicação e concorrência. "
            "Cada item listado merece análise da justificativa oficial do processo."
        ),
    )
    st.plotly_chart(
        sparkline(_anos, _acima_serie, "#E91E63"), use_container_width=True, config=SPARK_CFG, key="spark_lic_acima"
    )
with c2:
    st.metric(
        "Total sem processo licitatório",
        len(lacunas),
        delta=pct_delta(_totals_serie),
        delta_color="inverse",
        help=(
            "Total de contratos identificados sem número de licitação associado. Nem todos são "
            "irregulares — a lei permite contratação direta por dispensa (baixo valor, emergência) "
            "ou inexigibilidade (fornecedor exclusivo, profissional notório). O número alto é um "
            "ponto de atenção, não uma irregularidade automática."
        ),
    )
    st.plotly_chart(
        sparkline(_anos, _totals_serie, "#FF9800"), use_container_width=True, config=SPARK_CFG, key="spark_lic_total"
    )
with c3:
    st.metric(
        "Adesões de Ata (licitações)",
        _hist_adesao[year],
        delta=pct_delta(_adesao_serie),
        delta_color="inverse",
        help=(
            "Quantidade de contratos firmados por adesão à Ata de Registro de Preços — mecanismo "
            "em que a prefeitura aproveita uma licitação já realizada por ela mesma para novas "
            "compras, sem precisar abrir um novo processo. É uma forma legal e eficiente de "
            "contratar, desde que respeitados os limites de quantidade e vigência da ata."
        ),
    )
    st.plotly_chart(
        sparkline(_anos, _adesao_serie, "#9C27B0"), use_container_width=True, config=SPARK_CFG, key="spark_lic_adesao"
    )
with c4:
    st.metric(
        "Empenhos via Ata Externa",
        adesao_externa["quantidade"],
        delta=pct_delta(_adesao_ext_serie),
        delta_color="inverse",
        help=(
            "Empenhos identificados como 'carona em ata' — a prefeitura utilizou uma Ata de "
            "Registro de Preços aberta por outro ente público (outro município, estado ou órgão "
            "federal) para realizar a contratação. O chamado 'carona' é permitido pela Lei "
            "14.133/2021, mas exige autorização formal do órgão gerenciador da ata."
        ),
    )
    st.plotly_chart(
        sparkline(_anos, _adesao_ext_serie, "#607D8B"), use_container_width=True, config=SPARK_CFG, key="spark_lic_ext"
    )

# Preparar tabela de contratos sem licitação
lacunas_exibicao = lacunas.rename(
    columns={
        "fornecedor": "Fornecedor",
        "objeto": "Objeto",
        "valcon": "Valor",
        "periodo": "Período",
    }
)

with st.expander("Ver contratos sem processo licitatório"):
    # Remover coluna 'numero' (Nº)
    colunas_exibir = ["Fornecedor", "Objeto", "Valor", "Período"]
    df_exibir = lacunas_exibicao.drop(columns=["numero"], errors="ignore")
    st.dataframe(
        df_exibir[colunas_exibir],
        column_config={
            "Valor": st.column_config.NumberColumn(format="R$ %,.2f"),
        },
        width="stretch",
        hide_index=True,
    )

with st.expander("Ver licitações via Adesão de Ata"):
    if not adesao["lista"].empty:
        df_adesao = (
            adesao["lista"]
            .rename(
                columns={
                    "objeto": "Objeto",
                    "periodo": "Período",
                    "licitacao_valor": "Valor Est. Licitação",
                    "total_c_valor": "Valor Total Contratado",
                    "total_c_empenhado": "Valor Empenhado",
                    "tem_contrato": "Contrato Associado",
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
    if not adesao_externa["lista"].empty:
        st.caption(
            "Empenhos cuja justificativa contábil referencia uma Ata de Registro de Preços de outro ente "
            "(Termo de Adesão Externa). Esses registros complementam as licitações formais via carona."
        )
        st.dataframe(
            adesao_externa["lista"].rename(
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
        acima[["empresa", "fornecedor", "objeto", "valcon", "orgao_saude", "periodo"]].rename(
            columns={
                "empresa": "Entidade",
                "fornecedor": "Fornecedor",
                "objeto": "Objeto",
                "valcon": "Valor",
                "orgao_saude": "Saúde?",
                "periodo": "Período",
            }
        ),
        column_config={
            "Valor": st.column_config.NumberColumn(format="R$ %,.2f"),
            "Entidade": None,
        },
        width="stretch",
        hide_index=True,
    )
if not anomalias["fracionamento"].empty:
    st.subheader(":material/warning: Possível fracionamento de contratos")
    st.dataframe(
        anomalias["fracionamento"][["fornecedor", "valcon", "objeto", "periodo"]].rename(
            columns={
                "fornecedor": "Fornecedor",
                "valcon": "Valor",
                "objeto": "Objeto",
                "periodo": "Período",
            }
        ),
        column_config={
            "Valor": st.column_config.NumberColumn(format="R$ %,.2f"),
        },
        width="stretch",
        hide_index=True,
    )
st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
