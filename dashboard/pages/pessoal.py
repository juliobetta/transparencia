import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import fmt_currency, get_conn, get_extraction_date, render_partial_year_notice, render_sidebar
from sqlalchemy.engine import Engine

import glossary
from analysis import analise_despesas, payroll_vs_services
from analysis.analise_despesas import total_folha_por_orgao
from analysis.constants import LRF_PESSOAL_LIMITE_ALERTA, LRF_PESSOAL_LIMITE_LEGAL, LRF_PESSOAL_LIMITE_PRUDENCIAL

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _payroll(conn, year, _extracted_at):
    return payroll_vs_services.run(conn, list(range(2022, year + 1)))


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _departmental_payroll(conn, year, _extracted_at):
    return analise_despesas.get_folha_por_orgao(conn, year)


conn = get_conn()
year = render_sidebar()
_extracted_at = get_extraction_date(conn)

st.header("Folha de Pagamento")
st.caption(
    "Quanto da receita municipal arrecadada é comprometido com salários e proventos de servidores. "
    "A Lei de Responsabilidade Fiscal (LRF) limita esse gasto a **54% da receita corrente líquida** para o Poder Executivo. "
    "O cálculo usa o total de receitas arrecadadas como base — os dados do portal não permitem calcular a RCL exata com todas as deduções legais."
)
render_partial_year_notice(year, _extracted_at)
df = _payroll(conn, year, _extracted_at)
if not df.empty:
    fig = px.bar(
        df,
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

# Granular Salary Analysis
st.subheader("Distribuição de Remuneração")
st.info(
    "O portal não disponibiliza a remuneração líquida individual. "
    "O gráfico abaixo usa **Proventos** (remuneração bruta) como aproximação.",
    icon=":material/info:",
)
df_pessoal = payroll_vs_services.salary_distribution(conn, year)

if not df_pessoal.empty:
    fig_hist = px.histogram(
        df_pessoal,
        x="proventos",
        nbins=30,
        title="Distribuição dos Proventos Brutos",
        labels={"proventos": "Proventos (R$)"},
    )
    fig_hist.update_traces(hovertemplate="Proventos: R$ %{x:,.2f}<br>Servidores: %{y}")
    fig_hist.update_layout(yaxis_title="Nº de Servidores", xaxis_tickprefix="R$ ", xaxis_tickformat=",.0f")
    st.plotly_chart(fig_hist, width="stretch")
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

df_dept = _departmental_payroll(conn, year, _extracted_at)
if not df_dept.empty:
    st.metric("Total distribuído via responsáveis", fmt_currency(total_folha_por_orgao(df_dept)))

    fig_dept = px.bar(
        df_dept,
        x="pago",
        y="descricao",
        orientation="h",
        title=f"Folha distribuída por responsável ({year})",
        labels={"pago": "Total Pago (R$)", "descricao": "Responsável"},
    )
    fig_dept.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_dept, use_container_width=True)
else:
    st.info("Nenhum pagamento deste tipo registrado para este exercício.")

st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
