import sys
from datetime import date, datetime
from pathlib import Path

import glossary

sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.graph_objects as go
import streamlit as st
from streamlit.connections import SQLConnection

import db

ANO_INICIAL = 2021
ANO_ATUAL = date.today().year
ANOS = list(range(ANO_INICIAL, ANO_ATUAL + 1))
CIDADE_CLEAN = "PORCIUNCULA"  # TODO: move this to .env, keeping a default value


def get_conn():
    conn: SQLConnection = st.connection("postgresql", type="sql")
    return conn.engine


def get_data_extracao(engine) -> str | None:
    return db.get_metadata(engine, "last_extracted_at")


EMPRESA_PADRAO = "7"


def render_sidebar() -> tuple[int, str]:
    """Lê ano e entidade do session_state (definidos em app.py). Sem renderização de sidebar."""

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

    year = int(st.session_state.get("sidebar_year", ANOS[-1]))
    empresa_id = str(st.session_state.get("sidebar_empresa", EMPRESA_PADRAO))
    return year, empresa_id


def render_breadcrumb(year: int, empresa_id: str) -> None:
    nome = st.session_state.get("sidebar_empresa_nome", empresa_id)
    st.caption(f"{year} / {nome}")


def fmt_delta(d: dict, fmt: str = "{:+,.0f}") -> str:
    if d["pct"] is None:
        return "N/D"
    return f"{fmt.format(d['abs'])} ({d['pct']:+.1f}%)"


def fmt_currency(value: float) -> str:
    return f"R$ {value:,.2f}"


def fmt_compact(value: float) -> str:
    if abs(value) >= 1_000_000_000:
        return f"R$ {value / 1_000_000_000:.1f}bi"
    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:.1f}mi"
    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:.1f}mil"
    return f"R$ {value:,.0f}"


def fmt_percent(value: float) -> str:
    return f"{value:.2f}%"


SPARK_CFG: dict = {"displayModeBar": False, "staticPlot": True}


def pct_delta(series: list) -> str | None:
    """
    Calcula a variação percentual entre os dois últimos valores de uma série numérica.
    Retorna uma string formatada com o valor percentual, ou None se não houver dados suficientes.
    """
    if len(series) >= 2 and series[-2] != 0:
        return f"{(series[-1] - series[-2]) / series[-2] * 100:+.1f}%"
    return None


def sparkline(x: list, y: list, color: str = "#2196F3") -> go.Figure:
    """
    Exibe um gráfico de linha compacto (sparkline) usando Plotly, com preenchimento abaixo da linha.
    """
    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines", line=dict(color=color, width=2), fill="tozeroy"))
    fig.update_layout(
        height=80,
        margin=dict(l=0, r=0, t=4, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


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


_PT_MONTHS: list[str] = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def partial_year_month(extracted_at: str | None) -> str:
    """Return the Portuguese month abbreviation of the extraction date, or '?' on failure."""
    try:
        from pandas import Timestamp

        return _PT_MONTHS[int(Timestamp(extracted_at).month) - 2]
    except Exception:
        return "?"


def render_aviso_ano_parcial(year: int, extracted_at: str | None, extra_html: str = "") -> None:
    """
    Exibe um aviso estilizado explicando que o ano atual mostra dados de arrecadação parcial.
    """
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


def render_metodologia_receita() -> None:
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
