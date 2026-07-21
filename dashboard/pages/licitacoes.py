import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import (
    ANO_ATUAL,
    ANO_INICIAL,
    SPARK_CFG,
    get_conn,
    get_data_extracao,
    pct_delta,
    render_aviso_ano_parcial,
    render_breadcrumb,
    render_sidebar,
    sparkline,
)
from sqlalchemy.engine import Engine

import constants
import db
from analysis import adesao_de_ata, anomalias_contratuais, licitacao_gaps
from analysis import contratos as contratos_analysis
from analysis.constants import THRESHOLD_COMPRAS_SERVICOS

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _lacunas_licitacao(conn, year, empresa_ids, _extracted_at):
    return licitacao_gaps.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao(conn, year, empresa_ids, _extracted_at):
    return adesao_de_ata.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_externa(conn, year, empresa_ids, _extracted_at):
    return adesao_de_ata.run_external(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _anomalias(conn, year, empresa_ids, _extracted_at):
    return anomalias_contratuais.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _acima_por_ano(conn, years, empresa_ids, _extracted_at):
    return licitacao_gaps.counts_by_year(conn, list(years), empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _totals_sem_lic_por_ano(conn, years, empresa_ids, _extracted_at):
    return licitacao_gaps.totals_sem_licitacao_por_ano(conn, list(years), empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_por_ano(conn, years, empresa_ids, _extracted_at):
    return adesao_de_ata.formal_counts_by_year(conn, list(years), empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_ext_por_ano(conn, years, empresa_ids, _extracted_at):
    return adesao_de_ata.external_counts_by_year(conn, list(years), empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _modalidade(conn, year, empresa_ids, _extracted_at):
    return contratos_analysis.distribuicao_modalidade(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _fundlegal(conn, year, empresa_ids, _extracted_at):
    return contratos_analysis.distribuicao_fundamento_legal(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _top_fornecedores(conn, year, empresa_ids, _extracted_at):
    return contratos_analysis.top_fornecedores(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _baixa_execucao(conn, year, empresa_ids, _extracted_at):
    return contratos_analysis.contratos_baixa_execucao(conn, year, empresa_ids=empresa_ids)


conn = get_conn()
_orgaos = db.get_empresas(conn)
year, empresa_ids = render_sidebar()
_extracted_at = get_data_extracao(conn)

lacunas = _lacunas_licitacao(conn, year, empresa_ids, _extracted_at)
adesao = _adesao(conn, year, empresa_ids, _extracted_at)
adesao_externa = _adesao_externa(conn, year, empresa_ids, _extracted_at)
anomalias = _anomalias(conn, year, empresa_ids, _extracted_at)
df_modalidade = _modalidade(conn, year, empresa_ids, _extracted_at)
df_fundlegal = _fundlegal(conn, year, empresa_ids, _extracted_at)
df_top_forn = _top_fornecedores(conn, year, empresa_ids, _extracted_at)
df_baixa_exec = _baixa_execucao(conn, year, empresa_ids, _extracted_at)

acima = licitacao_gaps.filter_above_limit(lacunas)
saude = licitacao_gaps.filter_above_limit_health(lacunas)

_all_years = list(range(ANO_INICIAL, year + 1))
_anos = _all_years
_hist_acima = _acima_por_ano(conn, tuple(_all_years), empresa_ids, _extracted_at)
_hist_totals = _totals_sem_lic_por_ano(conn, tuple(_all_years), empresa_ids, _extracted_at)
_hist_adesao = _adesao_por_ano(conn, tuple(_all_years), empresa_ids, _extracted_at)
_hist_adesao_ext = _adesao_ext_por_ano(conn, tuple(_all_years), empresa_ids, _extracted_at)

_acima_serie = [_hist_acima[y] for y in _anos]
_totals_serie = [_hist_totals[y] for y in _anos]
_adesao_serie = [_hist_adesao[y] for y in _anos]
_adesao_ext_serie = [_hist_adesao_ext[y] for y in _anos]

st.header("Licitações e Contratos")
render_breadcrumb(year, empresa_ids)

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
        f"Acima do limite s/ licitação ({_limite_fmt})",
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
        "valor_contrato": "Valor",
        "periodo": "Período",
    }
)

with st.expander("Ver contratos sem processo licitatório"):
    df_exibir = lacunas.rename(
        columns={
            "fornecedor": "Fornecedor",
            "objeto": "Objeto",
            "valor_contrato": "Valor",
            "periodo": "Período",
            "modalidade": "Modalidade",
            "fundlegal": "Fundamento Legal",
        }
    )
    st.dataframe(
        df_exibir[["Fornecedor", "Objeto", "Modalidade", "Fundamento Legal", "Valor", "Período"]],
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
        _ext_exib = adesao_externa["lista"].copy()
        _ext_exib["unidade"] = _ext_exib["unidade"].astype(str).map(_orgaos).fillna(_ext_exib["unidade"])
        st.dataframe(
            _ext_exib.rename(
                columns={
                    "data": "Data",
                    "fornecedor": "Fornecedor",
                    "empenhado": "Valor Empenhado",
                    "pago": "Valor Pago",
                    "unidade": "Entidade",
                    "justificativa": "Justificativa Contábil",
                    "num_licitacao": "Nº Licitação",
                }
            ),
            column_config={
                "Valor Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Valor Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
            },
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Nenhum empenho com referência a ata externa registrado para este ano.")

with st.expander("Ver contratos acima do limite legal sem licitação"):
    if not acima.empty:
        st.caption(
            "Contratos abaixo do limite de dispensa são legais e não exigem licitação. "
            "O ponto de atenção está em contratos **acima** do limite sem processo formal — e especialmente "
            "quando o mesmo fornecedor aparece múltiplas vezes com valores próximos ao teto, "
            "o que pode indicar **fracionamento** (divisão artificial de compras para evitar licitação)."
        )
        _acima_exib = acima.copy()
        _acima_exib["empresa"] = _acima_exib["empresa"].astype(str).map(_orgaos).fillna(_acima_exib["empresa"])
        st.dataframe(
            _acima_exib[
                [
                    "empresa",
                    "numero",
                    "fornecedor",
                    "objeto",
                    "modalidade",
                    "fundlegal",
                    "valor_contrato",
                    "limite_dispensa",
                    "periodo",
                ]
            ].rename(
                columns={
                    "empresa": "Entidade",
                    "numero": "Nº Contrato",
                    "fornecedor": "Fornecedor",
                    "objeto": "Objeto",
                    "modalidade": "Modalidade",
                    "fundlegal": "Fundamento Legal",
                    "valor_contrato": "Valor",
                    "limite_dispensa": "Limite Dispensa",
                    "periodo": "Período",
                }
            ),
            column_config={
                "Valor": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Limite Dispensa": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Nenhum contrato acima do limite sem licitação identificado para este ano.")
with st.expander("Ver possível fracionamento de contratos"):
    if not anomalias["fracionamento"].empty:
        st.caption(
            "Fornecedores com 3 ou mais contratos próximos ao limite de dispensa no mesmo órgão, "
            "sugerindo possível fracionamento para evitar licitação."
        )
        _frac_exib = anomalias["fracionamento"].copy()
        _frac_exib["empresa"] = _frac_exib["empresa"].astype(str).map(_orgaos).fillna(_frac_exib["empresa"])
        st.dataframe(
            _frac_exib[
                [
                    "empresa",
                    "numero",
                    "fornecedor",
                    "objeto",
                    "modalidade",
                    "fundlegal",
                    "valor_contrato",
                    "limite",
                    "Período",
                ]
            ].rename(
                columns={
                    "empresa": "Entidade",
                    "numero": "Nº Contrato",
                    "fornecedor": "Fornecedor",
                    "objeto": "Objeto",
                    "modalidade": "Modalidade",
                    "fundlegal": "Fundamento Legal",
                    "valor_contrato": "Valor",
                    "limite": "Limite Dispensa",
                    "Período": "Período",
                }
            ),
            column_config={
                "Valor": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Limite Dispensa": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Nenhum possível fracionamento identificado para este ano.")

st.divider()

# ── Distribuição por Tipo de Contratação ─────────────────────────────────────
st.subheader("Distribuição por Tipo de Contratação")
col_mod, col_fund = st.columns(2)

with col_mod:
    if not df_modalidade.empty:
        fig_mod = px.bar(
            df_modalidade,
            x="valor",
            y="modalidade",
            orientation="h",
            text="contratos",
            labels={"valor": "Valor Total (R$)", "modalidade": "Modalidade", "contratos": "Nº Contratos"},
            title=f"Por Modalidade — {year}",
            color_discrete_sequence=["#3A7FC1"],
        )
        fig_mod.update_traces(texttemplate="%{text} contratos", textposition="outside", cliponaxis=False)
        fig_mod.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis=dict(tickprefix="R$ ", tickformat=",.0f"),
            margin=dict(l=0, r=130, t=40, b=0),
        )
        st.plotly_chart(fig_mod, use_container_width=True)

with col_fund:
    if not df_fundlegal.empty:
        fig_fund = px.bar(
            df_fundlegal,
            x="valor",
            y="fundlegal",
            orientation="h",
            text="contratos",
            labels={"valor": "Valor Total (R$)", "fundlegal": "Fundamento Legal", "contratos": "Nº Contratos"},
            title=f"Por Fundamento Legal — {year}",
            color_discrete_sequence=["#1C3A5E"],
        )
        fig_fund.update_traces(texttemplate="%{text} contratos", textposition="outside", cliponaxis=False)
        fig_fund.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis=dict(tickprefix="R$ ", tickformat=",.0f"),
            margin=dict(l=0, r=130, t=40, b=0),
        )
        st.plotly_chart(fig_fund, use_container_width=True)

# ── Top Fornecedores ──────────────────────────────────────────────────────────
with st.expander("Ver top fornecedores por valor contratado"):
    if not df_top_forn.empty:
        st.dataframe(
            df_top_forn.rename(
                columns={
                    "fornecedor_nome": "Fornecedor",
                    "contratos": "Nº Contratos",
                    "valor_total": "Valor Total",
                    "empenhado_total": "Valor Empenhado",
                }
            ),
            column_config={
                "Valor Total": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Valor Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Sem dados de fornecedores para este ano.")

# ── Contratos com Baixa Execução ──────────────────────────────────────────────
with st.expander("Ver contratos com baixa execução (< 20%)"):
    if not df_baixa_exec.empty:
        st.caption(
            "Contratos onde o valor empenhado é inferior a 20% do valor contratado. "
            "Pode indicar contratos parados, subdimensionados ou com execução atrasada."
        )
        _baixa_exib = df_baixa_exec.copy()
        _baixa_exib["empresa_id"] = _baixa_exib["empresa_id"].astype(str).map(_orgaos).fillna(_baixa_exib["empresa_id"])
        st.dataframe(
            _baixa_exib.rename(
                columns={
                    "empresa_id": "Entidade",
                    "contrato_numero": "Nº Contrato",
                    "fornecedor_nome": "Fornecedor",
                    "objeto": "Objeto",
                    "valor_contrato": "Valor",
                    "empenhado": "Empenhado",
                    "pct_execucao": "% Execução",
                }
            ),
            column_config={
                "Valor": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "% Execução": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
            },
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Nenhum contrato com baixa execução identificado para este ano.")

st.caption(f"[Ver no portal oficial →]({constants.PORTAL_URL})")
