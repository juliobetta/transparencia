import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from streamlit.connections import SQLConnection

import db
import glossary

YEARS = list(range(2022, date.today().year + 1))
CIDADE_CLEAN = "PORCIUNCULA"  # TODO: move this to .env, keeping a default value


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
        f"### :material/link: Portal Oficial\n[Ver fonte oficial →]({glossary.PORTAL_URL})",
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


def fmt_currency_short(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:,.1f}K"
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


_PT_MONTHS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def partial_year_month(extracted_at: str | None) -> str:
    """Return the Portuguese month abbreviation of the extraction date, or '?' on failure."""
    try:
        from pandas import Timestamp

        return _PT_MONTHS[Timestamp(extracted_at).month - 1]
    except Exception:
        return "?"


def render_partial_year_notice(year: int, extracted_at: str | None, extra_html: str = "") -> None:
    """Render a small styled notice explaining that `year` shows partial arrecadado data."""
    last_month = partial_year_month(extracted_at)
    body = (
        f"<strong>{year} exibe arrecadação real (parcial, Jan–{last_month}).</strong> "
        "Não é diretamente comparável aos anos anteriores, que mostram previsão orçamentária anual."
    )
    if extra_html:
        body += " " + extra_html
    st.markdown(
        "<div style='background:#dbeafe;border-left:4px solid #3b82f6;padding:0.4rem 0.75rem;"
        f"border-radius:4px;font-size:0.78rem;line-height:1.4;color:#1e3a5f;margin-bottom:0.5rem;'>"
        f"{body}</div>",
        unsafe_allow_html=True,
    )


def render_revenue_methodology() -> None:
    with st.expander(":material/info: Como os valores de receita são calculados?"):
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
