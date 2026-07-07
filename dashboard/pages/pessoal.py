import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import (
    ANO_ATUAL,
    SPARK_CFG,
    fmt_currency,
    get_conn,
    get_data_extracao,
    pct_delta,
    render_aviso_ano_parcial,
    render_sidebar,
    sparkline,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import analise_despesas, folha_vs_servicos
from analysis.analise_despesas import get_analise_intensidade_pessoal, total_folha_por_orgao
from analysis.constants import LRF_PESSOAL_LIMITE_ALERTA, LRF_PESSOAL_LIMITE_LEGAL, LRF_PESSOAL_LIMITE_PRUDENCIAL

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _folha_pagamento(conn, year, _extracted_at):
    return folha_vs_servicos.run(conn, list(range(2022, year + 1)))


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _folha_por_departamento(conn, year, _extracted_at):
    return analise_despesas.get_folha_por_orgao(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _folha_orgao_por_ano(conn, years, _extracted_at):
    return analise_despesas.total_folha_orgao_por_ano(conn, list(years))


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _analise_intensidade_pessoal(conn, years, _extracted_at):
    return get_analise_intensidade_pessoal(conn, list(years))


conn = get_conn()
year = render_sidebar()
_extracted_at = get_data_extracao(conn)

st.header("Folha de Pagamento")
st.caption(
    "Quanto da receita municipal arrecadada é comprometido com salários e proventos de servidores. "
    "A Lei de Responsabilidade Fiscal (LRF) limita esse gasto a **54% da receita corrente líquida** para o Poder Executivo. "
    "O cálculo usa o total de receitas arrecadadas como base — os dados do portal não permitem calcular a RCL exata com todas as deduções legais."
)

if year == ANO_ATUAL:
    render_aviso_ano_parcial(year, _extracted_at)

df_folha = _folha_pagamento(conn, year, _extracted_at)
_all_years = list(range(2022, year + 1))
_anos = _all_years
_hist_folha_orgao = _folha_orgao_por_ano(conn, tuple(_all_years), _extracted_at)
_folha_orgao_serie = [_hist_folha_orgao[y] for y in _anos]
if not df_folha.empty:
    _pct_serie = df_folha["percentual_folha"].tolist()
    _anos_folha = df_folha["ano"].tolist()
    _pct_atual = float(df_folha.iloc[-1]["percentual_folha"])
    kf1, _ = st.columns([1, 3])
    with kf1:
        st.metric(
            "Folha / Receita Arrecadada",
            f"{_pct_atual:.1f}%",
            delta=pct_delta(_pct_serie),
            delta_color="inverse",
            help="Percentual da receita arrecadada comprometido com folha de pessoal (proventos brutos).",
        )
        st.plotly_chart(
            sparkline(_anos_folha, _pct_serie, "#FF9800"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_pes_pct",
        )
    fig = px.bar(
        df_folha,
        x="ano",
        y="percentual_folha",
        title="Folha de Pessoal como % da Receita Arrecadada",
        labels={"ano": "Ano", "percentual_folha": "%"},
    )
    fig.update_xaxes(tickmode="linear", dtick=1)
    fig.update_traces(hovertemplate="Ano: %{x}<br>Percentual: %{y:.2f}%")
    fig.add_hline(
        y=LRF_PESSOAL_LIMITE_LEGAL,
        line_dash="solid",
        line_color="red",
        annotation_text=f"Limite legal {LRF_PESSOAL_LIMITE_LEGAL}%",
        annotation_position="top right",
    )
    fig.add_hline(
        y=LRF_PESSOAL_LIMITE_PRUDENCIAL,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"Limite prudencial {LRF_PESSOAL_LIMITE_PRUDENCIAL}%",
        annotation_position="top right",
    )
    fig.add_hline(
        y=LRF_PESSOAL_LIMITE_ALERTA,
        line_dash="dot",
        line_color="gold",
        annotation_text=f"Limite de alerta {LRF_PESSOAL_LIMITE_ALERTA}%",
        annotation_position="top right",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"Linhas de referência da Lei de Responsabilidade Fiscal: "
        f"**alerta** ({LRF_PESSOAL_LIMITE_ALERTA}%) · "
        f"**prudencial** ({LRF_PESSOAL_LIMITE_PRUDENCIAL}%, veda novos cargos e reajustes) · "
        f"**limite legal** ({LRF_PESSOAL_LIMITE_LEGAL}%, sujeito a sanções automáticas)"
    )

# Análise Granular de Remuneração
st.subheader("Distribuição de Remuneração")
st.info(
    "O portal não disponibiliza a remuneração líquida individual. "
    "O gráfico abaixo usa **Proventos** (remuneração bruta) como aproximação.",
    icon=":material/info:",
)
df_pessoal = folha_vs_servicos.distribuicao_salarios(conn, year)

if not df_pessoal.empty:
    fig_histograma = px.histogram(
        df_pessoal,
        x="proventos",
        nbins=30,
        title="Distribuição dos Proventos Brutos",
        labels={"proventos": "Proventos (R$)"},
    )
    fig_histograma.update_traces(hovertemplate="Proventos: R$ %{x:,.2f}<br>Servidores: %{y}")
    fig_histograma.update_layout(yaxis_title="Nº de Servidores", xaxis_tickprefix="R$ ", xaxis_tickformat=",.0f")
    st.plotly_chart(fig_histograma, width="stretch")
else:
    st.info("Dados de proventos não disponíveis para este exercício.")
st.divider()
st.subheader("Pagamentos via Responsáveis de Secretaria")
st.info(
    """
    **Por que uma pessoa aparece recebendo milhões de reais?**

    No Brasil, é prática comum em municípios que o ordenador de despesas de cada secretaria
    (o responsável pelo departamento) receba o montante total da folha de pagamento em seu CPF
    e o distribua entre os servidores da unidade. O sufixo **"E OUTROS"** no nome indica
    exatamente isso: o valor não é de uso pessoal — representa salários de toda a equipe.

    Esses pagamentos são **excluídos da análise de Fornecedores e Compras Locais** para não
    distorcer os índices de concentração e compras locais.
    """,
    icon=":material/info:",
)

df_departamentos = _folha_por_departamento(conn, year, _extracted_at)
if not df_departamentos.empty:
    _total_folha_atual = total_folha_por_orgao(df_departamentos)
    kp1, _ = st.columns([1, 3])
    with kp1:
        st.metric(
            "Total distribuído via responsáveis",
            fmt_currency(_total_folha_atual),
            delta=pct_delta(_folha_orgao_serie),
            delta_color="off",
        )
        st.plotly_chart(
            sparkline(_anos, _folha_orgao_serie, "#607D8B"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_pes_folha_orgao",
        )

    fig_departamentos = px.bar(
        df_departamentos,
        x="pago",
        y="descricao",
        orientation="h",
        title=f"Folha distribuída por responsável ({year})",
        labels={"pago": "Total Pago (R$)", "descricao": "Responsável"},
    )
    fig_departamentos.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_departamentos, use_container_width=True)
else:
    st.info("Nenhum pagamento deste tipo registrado para este exercício.")

st.divider()

# Intensidade de Pessoal por Órgão
st.subheader("Intensidade de Gastos com Pessoal")
st.info(
    "Compara o gasto total de cada órgão com os gastos específicos de folha de pessoal, "
    "calculando a porcentagem que a folha representa no orçamento total.",
    icon=":material/info:",
)

df_intensidade = _analise_intensidade_pessoal(conn, _all_years, _extracted_at)

if not df_intensidade.empty:
    df_plot = df_intensidade.copy()

    # Garante a ordenação cronológica e trata 'ano' como texto para evitar eixos numéricos contínuos (binning/2027)
    df_plot["ano_str"] = df_plot["ano"].astype(str)
    df_plot = df_plot.sort_values(["orgao", "ano"])

    fig_intensidade = px.line(
        df_plot,
        x="ano",
        y="pct_folha",
        color="orgao",
        title="Evolução da % do Orçamento comprometida com Folha por Órgão",
        labels={"pct_folha": "% do Orçamento", "orgao": "Órgão", "ano": "Ano"},
        markers=True,
        custom_data=["orgao", "gasto_total", "gasto_folha"],
    )

    # Tooltip customizado em português sem somas incorretas
    fig_intensidade.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>"
        + "Ano: %{x}<br>"
        + "Gasto Total: R$ %{customdata[1]:,.2f}<br>"
        + "Gasto Folha: R$ %{customdata[2]:,.2f}<br>"
        + "Intensidade (Folha/Total): %{y:.2f}%"
    )

    fig_intensidade.update_layout(
        xaxis=dict(title="Ano", tickmode="linear", dtick=1),
        yaxis=dict(title="% do Orçamento com Pessoal", ticksuffix="%"),
    )
    st.plotly_chart(fig_intensidade, use_container_width=True)

    st.write(f"### Detalhes do Exercício ({year})")
    df_ano = df_intensidade[df_intensidade["ano"] == year].copy()
    if not df_ano.empty:
        df_table = df_ano[["orgao", "gasto_total", "gasto_folha", "pct_folha"]].copy()
        df_table.columns = ["Órgão", "Gasto Total", "Gasto com Folha", "% do Orçamento"]

        st.dataframe(
            df_table.sort_values("% do Orçamento", ascending=False).style.format(
                {"Gasto Total": "R$ {:,.2f}", "Gasto com Folha": "R$ {:,.2f}", "% do Orçamento": "{:.2f}%"}
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(f"Sem dados detalhados disponíveis para o ano de {year}.")
else:
    st.info("Dados de intensidade não disponíveis para este exercício.")

st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
