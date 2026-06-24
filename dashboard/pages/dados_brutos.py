import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
from shared import get_conn, render_sidebar

import glossary

conn = get_conn()
year = render_sidebar()

_COLUMN_LABELS = {
    "ano": "Ano",
    "empresa": "Entidade",
    "codigo": "Código",
    "descricao": "Descrição",
    "empenhado": "Empenhado (R$)",
    "liquidado": "Liquidado (R$)",
    "pago": "Pago (R$)",
    "dotac": "Dotação Inicial (R$)",
    "altdo": "Alterações (R$)",
    "dotacao_atualizada": "Dotação Atualizada (R$)",
    "numero": "Número",
    "modalidade": "Modalidade",
    "objeto": "Objeto",
    "valor": "Valor (R$)",
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
    "proventos": "Proventos (R$)",
    "descontos": "Descontos (R$)",
    "previsto": "Previsto (R$)",
    "arrecadado": "Arrecadado (R$)",
    "previsao_inicial": "Previsão Inicial (R$)",
    "previsao_atualizada": "Previsão Atualizada (R$)",
    "arrecadado_periodo": "Arrecadado no Período (R$)",
    "arrecadado_total": "Arrecadado Total (R$)",
}

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
df = pd.read_sql_query(f"SELECT * FROM {table} WHERE ano = ?", conn, params=(year,))
st.dataframe(df.fillna("N/D").rename(columns=_COLUMN_LABELS), use_container_width=True)
st.download_button("Baixar CSV", df.to_csv(index=False).encode(), file_name=f"{table}_{year}.csv", mime="text/csv")
st.caption(f"Fonte: [Portal de Transparência]({glossary.PORTAL_URL})")
