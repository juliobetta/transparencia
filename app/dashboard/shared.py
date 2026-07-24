import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.graph_objects as go
import streamlit as st
from streamlit.connections import SQLConnection

import constants
import db

ANO_ATUAL = date.today().year

# Design token colors — Plotly-compatible hex equivalents of the CSS oklch palette
COLOR_ACCENT = "#3a7fc1"  # oklch(0.55 0.11 250) — civic blue
COLOR_POSITIVE = "#2e7d4f"  # oklch(0.5 0.13 145) — green
COLOR_ALERT = "#c47c1a"  # oklch(0.65 0.13 65) — orange
COLOR_RISK = "#b84040"  # oklch(0.55 0.11 25) — red
_portal_cfg = st.session_state.get("portal_config")
ANO_INICIAL: int = _portal_cfg.ano_inicial if _portal_cfg is not None else 2021
ANOS = list(range(ANO_INICIAL, ANO_ATUAL + 1))
del _portal_cfg


def get_conn():
    conn: SQLConnection = st.connection("postgresql", type="sql")
    return conn.engine


def _portal_slug() -> str:
    cfg = st.session_state.get("portal_config")
    return cfg.slug if cfg is not None else "porciuncula_prefeitura"


def get_data_extracao(engine) -> str | None:
    return db.get_metadata(engine, "last_extracted_at", _portal_slug())


def render_sidebar() -> tuple[int, list[str] | None]:
    """Lê ano e entidades do session_state (definidos em app.py). Sem renderização de sidebar."""

    engine = get_conn()
    _last_extracted = db.get_metadata(engine, "last_extracted_at", _portal_slug())
    if _last_extracted:
        fmt = "%Y-%m-%d %H:%M:%S" if " " in _last_extracted else "%Y-%m-%d"
        _last_extracted = datetime.strptime(_last_extracted, fmt).strftime("%d/%m/%Y %H:%M")
    st.sidebar.html(
        f'<div style="padding:10px 18px 12px;border-top:1px solid #f0f1f4;margin-top:4px">'
        f'<a href="{constants.PORTAL_URL}" target="_blank" style="font-size:12px;font-weight:600;color:#1a1d21;text-decoration:none">'
        f"Portal oficial da transparência ↗</a>"
        f'<div style="font-size:10.5px;color:#9aa1ab;margin-top:4px">'
        f"{'Última extração: ' + _last_extracted if _last_extracted else 'Última extração: desconhecida'}"
        f"</div></div>"
    )

    year = int(st.session_state.get("sidebar_year", ANOS[-1]))
    empresa_ids: list[str] | None = st.session_state.get("sidebar_empresa_ids", None)
    return year, empresa_ids


def render_breadcrumb(year: int, empresa_ids: list[str] | None) -> None:
    _empresas: dict = st.session_state.get("_empresas", {})
    _emp_ids = list(_empresas.keys())
    _emp_labels = list(_empresas.values())
    _years = list(reversed(range(ANO_INICIAL, ANO_ATUAL + 1)))
    current_nomes: list[str] = st.session_state.get("sidebar_empresa_nomes", [])

    c1, c2 = st.columns([1, 4])
    with c1:
        new_year: int = st.selectbox("Ano", _years, index=_years.index(year))
        if new_year != year:
            st.session_state["sidebar_year"] = new_year
            st.rerun()
    with c2:
        new_labels: list[str] = st.multiselect("Entidades", _emp_labels, default=current_nomes)
        new_ids = [_emp_ids[_emp_labels.index(label)] for label in new_labels]
        new_ids_or_none: list[str] | None = new_ids if new_ids else None
        # Normaliza: vazio e None representam o mesmo estado (todas as entidades)
        current_set = set(empresa_ids) if empresa_ids else set(_emp_ids)
        new_set = set(new_ids) if new_ids else set(_emp_ids)
        if new_set != current_set:
            st.session_state["sidebar_empresa_ids"] = new_ids_or_none
            st.session_state["sidebar_empresa_nomes"] = new_labels
            st.rerun()


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


def sparkline(x: list, y: list, color: str = COLOR_ACCENT) -> go.Figure:
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
    st.html(alert_box(body, kind="info"))


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


# ── Design system helpers ─────────────────────────────────────────────────────


def kpi_card(label: str, valor: str, sub: str = "", accent: bool = False, risk: bool = False) -> str:
    cor = "var(--risk)" if risk else ("var(--accent)" if accent else "var(--ink)")
    return (
        f'<div style="background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px">'
        f'<div style="font-size:12px;color:var(--muted);margin-bottom:4px;line-height:1.3">{label}</div>'
        f'<div class="serif" style="font-weight:700;font-size:26px;line-height:1;color:{cor}">{valor}</div>'
        f'<div style="font-size:11px;color:var(--subtle);margin-top:4px">{sub}</div>'
        f"</div>"
    )


def kpi_grid(*cards: str, cols: int = 4) -> str:
    inner = "".join(f"<div>{c}</div>" for c in cards)
    return f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:14px;margin-bottom:1.5rem">{inner}</div>'


def chip(label: str, kind: str = "default") -> str:
    styles: dict[str, str] = {
        "dispensa": "background:#fdf3e7;color:#7a5320",
        "inexigibilidade": "background:#eef4fd;color:#3a5a86",
        "pregao": "background:oklch(0.55 0.11 250 / 0.12);color:oklch(0.4 0.12 250)",
        "concorrencia": "background:#f0f4ff;color:#3b4a80",
        "adesao": "background:#f3f0ff;color:#5a4080",
        "default": "background:#f0f1f4;color:#4b5563",
    }
    s = styles.get(kind.lower(), styles["default"])
    return (
        f'<span style="{s};border-radius:20px;padding:3px 9px;'
        f'font-size:11px;font-weight:600;display:inline-block">{label}</span>'
    )


def alert_box(body: str, kind: str = "info") -> str:
    _bg = {"info": "#eef4fd", "warning": "#fdf3e7", "risk": "#fdecea"}
    _bdr = {"info": "oklch(0.55 0.11 250)", "warning": "oklch(0.65 0.13 65)", "risk": "oklch(0.55 0.11 25)"}
    _txt = {"info": "#3a5a86", "warning": "#7a5320", "risk": "#7a2020"}
    bg = _bg.get(kind, _bg["info"])
    bdr = _bdr.get(kind, _bdr["info"])
    txt = _txt.get(kind, _txt["info"])
    return (
        f'<div style="background:{bg};border-left:4px solid {bdr};border-radius:6px;'
        f'padding:11px 15px;font-size:12.5px;line-height:1.5;color:{txt};margin-bottom:1.25rem">'
        f"{body}</div>"
    )


def page_header(eyebrow: str, title: str, description: str = "") -> str:
    desc_html = (
        f'<p style="font-size:14px;line-height:1.6;color:#5a626c;margin:8px 0 26px;max-width:64ch">{description}</p>'
        if description
        else ""
    )
    return (
        f'<div style="font-size:11px;font-weight:600;letter-spacing:.09em;color:oklch(0.55 0.11 250);'
        f'text-transform:uppercase;margin-bottom:12px">{eyebrow}</div>'
        f'<h1 class="serif" style="font-weight:700;font-size:34px;line-height:1.1;'
        f'letter-spacing:-.01em;margin:0">{title}</h1>'
        f"{desc_html}"
    )


def section_heading(title: str, aside: str = "", numbered: str = "", aside_href: str = "") -> str:
    num_html = (
        f'<span class="serif" style="font-weight:700;font-size:22px;'
        f'color:oklch(0.55 0.11 250);margin-right:12px">{numbered}</span>'
        if numbered
        else ""
    )
    if aside:
        _aside_inner = (
            f'<a href="{aside_href}" target="_top" style="color:inherit;text-decoration:none;cursor:pointer">{aside}</a>'
            if aside_href
            else aside
        )
        aside_html = f'<span style="font-size:11.5px;color:var(--subtle)">{_aside_inner}</span>'
    else:
        aside_html = ""
    return (
        f'<div style="display:flex;align-items:baseline;justify-content:space-between;'
        f'border-top:2px solid var(--ink);padding-top:12px;margin:1.5rem 0 1rem">'
        f'<h3 class="serif" style="margin:0;font-weight:700;font-size:20px">{num_html}{title}</h3>'
        f"{aside_html}</div>"
    )


def barra_comparativa(
    rows: list[tuple[str, float, float, float]],
    label_prev: str = "Previsto",
    label_arr: str = "Arrecadado",
) -> str:
    """Dual horizontal bar per row: (label, previsto, arrecadado, max_value)."""
    legend = (
        f'<div style="display:flex;gap:16px;font-size:11.5px;color:var(--muted);margin-bottom:16px">'
        f'<span style="display:flex;align-items:center;gap:6px">'
        f'<span style="width:10px;height:10px;border-radius:2px;background:#d5dbe6"></span>{label_prev}</span>'
        f'<span style="display:flex;align-items:center;gap:6px">'
        f'<span style="width:10px;height:10px;border-radius:2px;background:oklch(0.55 0.11 250)"></span>{label_arr}</span>'
        f"</div>"
    )
    items = []
    for label, previsto, arrecadado, max_val in rows:
        pct_prev = min(previsto / max_val * 100, 100) if max_val > 0 else 0
        pct_arr = min(arrecadado / max_val * 100, 100) if max_val > 0 else 0
        pct_real = arrecadado / previsto * 100 if previsto > 0 else 0
        items.append(
            f"<div>"
            f'<div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:8px">'
            f'<strong style="font-weight:600">{label}</strong>'
            f'<span style="color:var(--muted)">{pct_real:.0f}% realizado</span></div>'
            f'<div style="height:14px;background:#eef0f4;border-radius:4px;margin-bottom:5px;overflow:hidden">'
            f'<div style="width:{pct_prev:.1f}%;height:100%;background:#d5dbe6;border-radius:4px"></div></div>'
            f'<div style="height:14px;background:#eef0f4;border-radius:4px;overflow:hidden">'
            f'<div style="width:{pct_arr:.1f}%;height:100%;background:oklch(0.55 0.11 250);border-radius:4px"></div></div>'
            f"</div>"
        )
    inner = f'<div style="display:flex;flex-direction:column;gap:22px">{"".join(items)}</div>'
    return (
        f'<div style="background:var(--card);border:1px solid var(--line);border-radius:14px;'
        f'padding:24px 26px;margin-bottom:1.5rem">{legend}{inner}</div>'
    )


def bar_chart_h(rows: list[tuple[str, float, str]]) -> str:
    """Horizontal bar chart: list of (label, value, formatted_value). Bars are proportional to max."""
    max_val = max((v for _, v, _ in rows), default=1)
    n = len(rows)
    blue_steps = [
        f"oklch({min(0.55 + i * 0.04, 0.74):.2f} {max(0.08, 0.11 - i * 0.01):.2f} {max(200, 250 - i * 8)})"
        for i in range(n)
    ]
    cells = []
    for i, (label, value, fmt_val) in enumerate(rows):
        pct = value / max_val * 100 if max_val > 0 else 0
        _parts = fmt_val.split(" · ", 1)
        if len(_parts) == 2:
            _val_html = (
                f'<span style="color:#6b7280;font-weight:400">{_parts[0]}</span>'
                f'<span style="color:#6b7280;font-weight:400"> · </span>'
                f'<span style="color:#1a1d21;font-weight:700">{_parts[1]}</span>'
            )
        else:
            _val_html = f'<span style="color:#1a1d21;font-weight:700">{fmt_val}</span>'
        cells.append(
            f'<span style="overflow:hidden;white-space:nowrap;text-overflow:ellipsis;font-size:12.5px;color:#4b5563;align-self:center">{label.title()}</span>'
            f'<div style="height:20px;background:#eef0f4;border-radius:4px;overflow:hidden;align-self:center">'
            f'<div style="width:{pct:.1f}%;height:100%;background:{blue_steps[i]};border-radius:4px"></div></div>'
            f"<span style=\"white-space:nowrap;text-align:right;font-family:'Source Serif 4',serif;"
            f'font-size:14px;align-self:center">{_val_html}</span>'
        )
    return (
        f'<div style="background:var(--card);border:1px solid var(--line);border-radius:14px;'
        f"padding:22px 26px;display:grid;grid-template-columns:160px 1fr auto;"
        f'gap:10px 14px;align-items:center">'
        f"{''.join(cells)}</div>"
    )


def donut_conic(
    segments: list[tuple[str, float, str]],
    center_label: str = "",
    center_sub: str = "",
) -> str:
    """CSS conic-gradient donut with legend. segments: (label, percentage 0–100, color)."""
    stops = []
    cur = 0.0
    for _, pct, color in segments:
        stops.append(f"{color} {cur:.1f}% {cur + pct:.1f}%")
        cur += pct
    gradient = ",".join(stops)
    legend_items = "".join(
        f'<div style="display:flex;align-items:center;gap:8px;font-size:12.5px;margin-bottom:3px">'
        f'<span style="width:9px;height:9px;border-radius:2px;background:{color};flex-shrink:0"></span>'
        f'<span style="flex:1">{label}</span>'
        f'<strong style="font-weight:600">{pct:.0f}%</strong></div>'
        for label, pct, color in segments
    )
    center_html = (
        (
            f'<div class="serif" style="font-weight:700;font-size:19px;line-height:1">{center_label}</div>'
            f'<div style="font-size:9px;color:var(--subtle)">{center_sub}</div>'
        )
        if center_label
        else ""
    )
    return (
        f'<div style="display:flex;align-items:center;gap:24px">'
        f'<div style="width:120px;height:120px;border-radius:50%;flex-shrink:0;'
        f'background:conic-gradient({gradient});display:flex;align-items:center;justify-content:center">'
        f'<div style="width:72px;height:72px;border-radius:50%;background:var(--card);'
        f'display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">'
        f"{center_html}</div></div>"
        f'<div style="flex:1">{legend_items}</div></div>'
    )


def funnel_waterfall(steps: list[tuple[str, float, str]], dotacao: float) -> str:
    """Horizontal waterfall: steps = (label, value, formatted_value). Widths proportional to dotacao."""
    items = []
    for label, value, fmt_val in steps:
        pct = value / dotacao * 100 if dotacao > 0 else 100
        items.append(
            f'<div style="flex:1">'
            f'<div style="font-size:12px;color:var(--muted);margin-bottom:7px">{label}</div>'
            f'<div style="height:11px;background:#eef0f4;border-radius:4px;overflow:hidden">'
            f'<div style="width:{pct:.0f}%;height:100%;background:oklch(0.55 0.11 250);border-radius:4px"></div></div>'
            f'<div class="serif" style="margin-top:8px;font-weight:700;font-size:19px">{fmt_val}</div>'
            f'<div style="font-size:11px;color:var(--subtle)">{pct:.0f}% da dotação</div>'
            f"</div>"
        )
    arrow = '<div style="width:26px;align-self:flex-start;text-align:center;color:#c7ccd4;padding-top:2px;font-size:18px">›</div>'
    inner = arrow.join(items)
    return (
        f'<div style="background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px 26px 24px">'
        f'<div style="display:flex;gap:2px">{inner}</div></div>'
    )


def dense_table(columns: list[str], rows: list[list], footer: str = "") -> str:
    """HTML table with chip support. Rows are lists; dict elements render as chip()."""
    th = "".join(
        f'<th style="padding:11px 14px;font-weight:600;'
        f'{"text-align:right;" if i > 0 else "padding-left:18px;"}">{c}</th>'
        for i, c in enumerate(columns)
    )
    trs = []
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            align = "" if i == 0 else "text-align:right;"
            pad = "padding:12px 18px;" if i == 0 else "padding:12px 14px;"
            if isinstance(cell, dict):
                inner_html = chip(cell.get("label", ""), cell.get("kind", "default"))
                cells.append(f'<td style="{pad}">{inner_html}</td>')
            else:
                serif = "font-family:'Source Serif 4',serif;font-weight:700;" if i == len(row) - 2 else ""
                cells.append(f'<td style="{pad}{align}{serif}">{cell}</td>')
        trs.append(f'<tr style="border-top:1px solid #f0f1f4">{"".join(cells)}</tr>')
    footer_html = (
        f'<div style="padding:12px 18px;border-top:1px solid #f0f1f4;font-size:12px;color:var(--subtle)">{footer}</div>'
        if footer
        else ""
    )
    return (
        f'<div style="background:var(--card);border:1px solid var(--line);border-radius:14px;'
        f'overflow:hidden;margin-bottom:1.5rem">'
        f'<table style="width:100%;border-collapse:collapse;font-size:12.5px">'
        f'<thead><tr style="background:#f8f9fb;color:var(--muted);font-size:10.5px;'
        f'text-transform:uppercase;letter-spacing:.05em;text-align:left">'
        f"{th}</tr></thead>"
        f"<tbody>{''.join(trs)}</tbody>"
        f"</table>{footer_html}</div>"
    )


def plotly_card_layout(title: str = "", height: int = 300, margin: dict | None = None) -> dict:
    """Return Plotly layout kwargs that match the design-system card style (transparent bg, IBM Plex Sans font)."""
    m = margin or dict(l=16, r=16, t=36 if title else 16, b=16)
    base: dict = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, sans-serif", color="#1a1d21", size=12),
        margin=m,
        height=height,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5, font=dict(size=11)),
    )
    if title:
        base["title"] = dict(text=title, font=dict(family="Source Serif 4, serif", size=15, color="#1a1d21"))
    return base


def plotly_card_start() -> str:
    return '<div style="background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px 8px;margin-bottom:1.5rem;overflow:hidden">'


def plotly_card_end() -> str:
    return "</div>"
