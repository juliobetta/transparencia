from __future__ import annotations

import io
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd
from fpdf import FPDF
from fpdf.fonts import FontFace

sys.path.insert(0, str(Path(__file__).parent.parent))

import db
from analysis import health_story

ASSETS_DIR = Path(__file__).parent.parent / "assets"
BRASAO_PATH = ASSETS_DIR / "brasao-porciuncula.svg"

BLUE_DARK = (26, 82, 118)
BLUE_MID = (26, 122, 191)
GRAY_LIGHT = (240, 244, 248)
GRAY_TEXT = (102, 102, 102)
WARN_BG = (255, 243, 205)


def _fmt_brl(value: float) -> str:
    return f"R$ {value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _section_header(pdf: FPDF, title: str) -> None:
    pdf.set_fill_color(*BLUE_DARK)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, title, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_text_color(0, 0, 0)


def _metric_row(pdf: FPDF, cards: list[tuple[str, str]]) -> None:
    n = len(cards)
    gap = 4.0
    w = (pdf.epw - gap * (n - 1)) / n
    start_x = pdf.l_margin
    start_y = pdf.get_y()

    for i, (label, value) in enumerate(cards):
        x = start_x + i * (w + gap)
        pdf.set_xy(x, start_y)
        pdf.set_fill_color(*GRAY_LIGHT)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*GRAY_TEXT)
        pdf.cell(w, 6, label, fill=True, new_x="RIGHT", new_y="TOP")
        pdf.set_xy(x, start_y + 6)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*BLUE_DARK)
        pdf.cell(w, 8, value, fill=True)

    pdf.set_xy(pdf.l_margin, start_y + 18)


def _budget_chart_png(budget_trend: pd.DataFrame) -> bytes:
    anos = budget_trend["ano"].astype(str).tolist()
    dotacao = (budget_trend["dotacao"] / 1e6).tolist()
    empenhado = (budget_trend["empenhado"] / 1e6).tolist()
    x = list(range(len(anos)))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7, 2.8))
    ax.bar([i - w / 2 for i in x], dotacao, w, label="Dotação", color="#1a7abf", alpha=0.85)
    ax.bar([i + w / 2 for i in x], empenhado, w, label="Empenhado", color="#1a5276")
    ax.set_xticks(x)
    ax.set_xticklabels(anos, fontsize=8)
    ax.set_ylabel("R$ milhões", fontsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.legend(fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.5)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _draw_orcamento_section(pdf: FPDF, budget: dict, budget_trend: pd.DataFrame) -> None:
    _section_header(pdf, "1. ORÇAMENTO & EXECUÇÃO")
    _metric_row(
        pdf,
        [
            ("Dotação Atualizada", _fmt_brl(budget["dotacao"])),
            ("Total Empenhado", _fmt_brl(budget["empenhado"])),
            ("Taxa de Execução", f"{budget['taxa_execucao']:.1%}"),
        ],
    )
    if budget.get("flag_under_execution"):
        pdf.set_fill_color(*WARN_BG)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 6, "⚠  Taxa de execução abaixo de 70% para ano encerrado.", fill=True)
        pdf.ln(3)
    if not budget_trend.empty and len(budget_trend) >= 2:
        chart_bytes = _budget_chart_png(budget_trend)
        pdf.image(io.BytesIO(chart_bytes), w=pdf.epw)
    pdf.ln(5)


def _draw_emendas_section(pdf: FPDF, emendas: pd.DataFrame, emendas_total: float) -> None:
    _section_header(pdf, "2. EMENDAS PARLAMENTARES")
    if emendas_total <= 0:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, "Sem emendas parlamentares registradas.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        return

    _metric_row(pdf, [("Total Recebido (Valor Autorizado)", _fmt_brl(emendas_total))])

    if emendas.empty:
        pdf.ln(2)
        return

    headings_style = FontFace(fill_color=BLUE_DARK, color=(255, 255, 255), emphasis="BOLD", size_pt=9)
    with pdf.table(
        col_widths=[65, 65, 27, 23],
        headings_style=headings_style,
        line_height=5,
        first_row_as_headings=True,
    ) as table:
        hdr = table.row()
        for col in ["Autor", "Ato Normativo", "Autorizado (R$)", "Empenhado (R$)"]:
            hdr.cell(col)
        for _, r in emendas.iterrows():
            row = table.row()
            row.cell(str(r.get("Autor", "")))
            row.cell(str(r.get("Ato Normativo", "")))
            row.cell(_fmt_brl(float(r.get("Valor Autorizado", 0) or 0)))
            emp = r.get("Empenhado")
            row.cell(_fmt_brl(float(emp)) if pd.notna(emp) and emp else "-")
    pdf.ln(5)


def _draw_fornecedores_section(pdf: FPDF, top_suppliers: pd.DataFrame, hhi: float) -> None:
    _section_header(pdf, "3. FORNECEDORES & CONCENTRAÇÃO DE MERCADO")
    hhi_label = "baixo" if hhi < 1500 else ("moderado" if hhi < 2500 else "alto")
    _metric_row(pdf, [("Indice HHI (concentracao de mercado)", f"{hhi:,.0f} - {hhi_label}")])

    if top_suppliers.empty:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, "Sem dados de fornecedores.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        return

    headings_style = FontFace(fill_color=BLUE_DARK, color=(255, 255, 255), emphasis="BOLD", size_pt=9)
    with pdf.table(
        col_widths=[100, 45, 35],
        headings_style=headings_style,
        line_height=5,
        first_row_as_headings=True,
    ) as table:
        hdr = table.row()
        for col in ["Fornecedor", "Empenhado (R$)", "% do Total"]:
            hdr.cell(col)
        for _, r in top_suppliers.head(10).iterrows():
            row = table.row()
            row.cell(str(r.get("descricao", "")))
            row.cell(_fmt_brl(float(r.get("empenhado", 0) or 0)))
            pct = float(r.get("percentual", 0) or 0)
            row.cell(f"{pct:.1f}%")
    pdf.ln(5)


class _SaudePDF(FPDF):
    def __init__(self, year: int, last_extracted: str) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.year = year
        self.last_extracted = last_extracted
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self) -> None:
        if BRASAO_PATH.exists():
            try:
                self.image(str(BRASAO_PATH), x=15, y=10, h=20)
            except Exception:
                pass
        self.set_xy(40, 10)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*BLUE_DARK)
        self.cell(0, 7, f"Fundo Municipal de Sa\xfade \x96 {self.year}", new_x="LMARGIN", new_y="NEXT")
        self.set_xy(40, 17)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*GRAY_TEXT)
        self.cell(0, 5, "Município de Porciúncula / RJ", new_x="LMARGIN", new_y="NEXT")
        self.set_xy(40, 22)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, f"Dados extraídos em: {self.last_extracted}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*BLUE_DARK)
        self.line(15, 36, 195, 36)
        self.set_xy(self.l_margin, 42)
        self.set_text_color(0, 0, 0)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRAY_TEXT)
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 10, f"Gerado em: {now}   |   Página {self.page_no()}", align="C")


def generate(conn: Any, year: int) -> bytes:
    data = health_story.run(conn, year)
    _raw = db.get_metadata(conn, "last_extracted_at")
    last_extracted = datetime.fromisoformat(_raw).strftime("%d/%m/%Y") if _raw else "desconhecida"

    pdf = _SaudePDF(year=year, last_extracted=last_extracted)
    pdf.add_page()

    _draw_orcamento_section(pdf, data["budget"], data["budget_trend"])
    _draw_emendas_section(pdf, data["emendas"], data["emendas_total"])
    _draw_fornecedores_section(pdf, data["top_suppliers"], data["hhi"])

    return bytes(pdf.output())
