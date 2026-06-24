import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

st.set_page_config(page_title="Transparência Porciúncula", layout="wide")

pages = [
    st.Page("pages/visao_geral.py", title="Visão Geral"),
    st.Page("pages/saude.py", title="Narrativa: Saúde"),
    st.Page("pages/orcamento.py", title="Execução Orçamentária"),
    st.Page("pages/fornecedores.py", title="Fornecedores"),
    st.Page("pages/licitacoes.py", title="Licitações e Contratos"),
    st.Page("pages/receitas.py", title="Receitas"),
    st.Page("pages/pessoal.py", title="Pessoal"),
    st.Page("pages/comparacao.py", title="Comparação"),
    st.Page("pages/dados_brutos.py", title="Dados Brutos"),
]
pg = st.navigation(pages)
pg.run()
