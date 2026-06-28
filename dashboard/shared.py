import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from streamlit.connections import SQLConnection

import db
import glossary

YEARS = list(range(2022, date.today().year + 1))


def get_conn():
    conn: SQLConnection = st.connection("postgresql", type="sql")
    return conn.engine


def get_extraction_date(engine) -> str | None:
    return db.get_metadata(engine, "last_extracted_at")


def render_sidebar() -> int:
    engine = get_conn()
    _last_extracted = db.get_metadata(engine, "last_extracted_at")
    if _last_extracted:
        fmt = "%Y-%m-%d %H:%M:%S" if " " in _last_extracted else "%Y-%m-%d"
        _last_extracted = datetime.strptime(_last_extracted, fmt).strftime("%d/%m/%Y %H:%M")
    st.sidebar.markdown(
        f"### 🔗 Portal Oficial\n[Ver fonte oficial →]({glossary.PORTAL_URL})",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"Última extração: **{_last_extracted}**" if _last_extracted else "Última extração: desconhecida"
    )
    return int(st.session_state.get("sidebar_year", YEARS[-1]))


def fmt_delta(d: dict, fmt: str = "{:+,.0f}") -> str:
    if d["pct"] is None:
        return "N/D"
    return f"{fmt.format(d['abs'])} ({d['pct']:+.1f}%)"


def fmt_currency(value: float) -> str:
    return f"R$ {value:,.2f}"


def fmt_percent(value: float) -> str:
    return f"{value:.2f}%"


def comparison_table(domain: dict, rows: list[tuple[str, str]]):
    import pandas as pd

    records = []
    for label, key in rows:
        d = domain[key]
        records.append(
            {
                "Métrica": label,
                "Período A": d["a"],
                "Período B": d["b"],
                "Δ Absoluto": d["abs"],
                "Δ %": d["pct"],
            }
        )
    return pd.DataFrame(records)


def render_revenue_methodology() -> None:
    with st.expander("ℹ️ Como os valores de receita são calculados?"):
        st.markdown(
            """
Os valores de receita são extraídos diretamente do portal de transparência municipal,
que segue a classificação orçamentária padrão SICONFI. Nesse padrão, cada receita é
registrada simultaneamente em múltiplos níveis hierárquicos — da categoria raiz até o
item mais detalhado — e todos coexistem na mesma tabela.

Para evitar dupla contagem, este painel considera apenas os **códigos de nível raiz**
de cada fonte, que representam o total consolidado sem sobreposição entre níveis
intermediários da hierarquia.

**Fontes utilizadas:**
- **Receita Própria** — tributos, taxas e outras receitas arrecadadas diretamente pelo município
- **Transferências da União** — repasses federais (FPM, FUNDEB, SUS, CIDE, etc.)
- **Transferências do Estado** — repasses estaduais (ICMS, IPVA, FECP, etc.)
            """
        )
