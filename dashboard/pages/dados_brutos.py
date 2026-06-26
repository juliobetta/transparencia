import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
from shared import get_conn, render_sidebar
from sqlalchemy import text

import glossary

conn = get_conn()
year = render_sidebar()

_COLUMN_LABELS = {
    "ano": "Ano",
    "empresa": "Entidade",
    "codigo": "Código",
    "descricao": "Descrição",
    "empenhado": "Empenhado",
    "liquidado": "Liquidado",
    "pago": "Pago",
    "dotac": "Dotação Inicial",
    "altdo": "Alterações",
    "dotacao_atualizada": "Dotação Atualizada",
    "numero": "Número",
    "modalidade": "Modalidade",
    "objeto": "Objeto",
    "valor": "Valor",
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
    "proventos": "Proventos",
    "descontos": "Descontos",
    "previsto": "Previsto",
    "arrecadado": "Arrecadado",
    "previsao_inicial": "Previsão Inicial",
    "previsao_atualizada": "Previsão Atualizada",
    "arrecadado_periodo": "Arrecadado no Período",
    "arrecadado_total": "Arrecadado Total",
}

_CURRENCY_COLUMNS = [
    "empenhado",
    "liquidado",
    "pago",
    "dotac",
    "altdo",
    "dotacao_atualizada",
    "valor",
    "proventos",
    "descontos",
    "previsto",
    "arrecadado",
    "previsao_inicial",
    "previsao_atualizada",
    "arrecadado_periodo",
    "arrecadado_total",
]

_TABLE_LABELS = {
    "despesas_por_orgao": "Despesas por Órgão",
    "despesas_por_fornecedor": "Despesas por Fornecedor",
    "licitacoes": "Licitações",
    "contratos": "Contratos",
    "pessoal": "Pessoal",
    "receita_orcamentaria": "Receita Orçamentária",
}

st.header("Dados Brutos")
allowed_tables = list(_TABLE_LABELS.keys())
table = st.selectbox("Tabela", allowed_tables, format_func=lambda t: _TABLE_LABELS[t])
if table not in allowed_tables:
    raise ValueError(f"Tabela inválida: {table}")
df = pd.read_sql_query(text(f"SELECT * FROM {table} WHERE ano = :ano"), conn, params={"ano": year})
config = {
    _COLUMN_LABELS[col]: st.column_config.NumberColumn(format="R$ %,.2f")
    for col in df.columns
    if col in _CURRENCY_COLUMNS
}
st.dataframe(df.fillna("N/D").rename(columns=_COLUMN_LABELS), column_config=config, width="stretch")
st.download_button("Baixar CSV", df.to_csv(index=False).encode(), file_name=f"{table}_{year}.csv", mime="text/csv")
st.caption(f"Fonte: [Portal de Transparência]({glossary.PORTAL_URL})")
