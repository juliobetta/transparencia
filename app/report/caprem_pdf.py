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
from app.analytics import historia_caprem
from config import PortalConfig

ASSETS_DIR = Path(__file__).parent.parent / "assets"
BRASAO_PATH = ASSETS_DIR / "brasao-porciuncula.svg"
FONTS_DIR = ASSETS_DIR / "fonts"

BLUE_ACCENT = (58, 127, 193)
BLUE_DARK = (28, 58, 94)
BLUE_MID = (37, 99, 160)
BLUE_LIGHT = (235, 243, 251)
GRAY_TEXT = (107, 114, 128)

FONT_SIZE_NORMAL = 9
FONT_SIZE_SMALL = 8
FONT_SIZE_HEADER = 11
FONT_SIZE_SUBHEADER = 10

_HEADING_STYLE = FontFace(fill_color=BLUE_MID, color=(255, 255, 255), emphasis="BOLD", size_pt=FONT_SIZE_NORMAL)
_ROW_WHITE = FontFace(fill_color=(255, 255, 255), size_pt=FONT_SIZE_NORMAL)


def _fmt_brl(value: float) -> str:
    return f"R$ {value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _section_header(pdf: FPDF, title: str) -> None:
    pdf.set_font("NotoSans", "B", FONT_SIZE_HEADER)
    pdf.set_text_color(*BLUE_ACCENT)
    pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_draw_color(*BLUE_ACCENT)
    pdf.set_line_width(0.4)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.l_margin + pdf.epw, y)
    pdf.set_line_width(0.2)
    pdf.ln(4)
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
        pdf.set_fill_color(*BLUE_LIGHT)
        pdf.set_font("NotoSans", "", FONT_SIZE_SMALL)
        pdf.set_text_color(*GRAY_TEXT)
        pdf.cell(w, 7, label, fill=True, new_x="RIGHT", new_y="TOP")
        pdf.set_xy(x, start_y + 7)
        pdf.set_font("NotoSans", "B", FONT_SIZE_HEADER)
        pdf.set_text_color(*BLUE_DARK)
        pdf.cell(w, 9, value, fill=True)

    pdf.set_xy(pdf.l_margin, start_y + 20)


def _trend_chart_png(trend: pd.DataFrame) -> bytes:
    anos = trend["ano"].astype(str).tolist()
    empenhado = (trend["empenhado"] / 1e6).tolist()
    pago = (trend["pago"] / 1e6).tolist()
    x = list(range(len(anos)))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7, 2.8))
    ax.bar([i - w / 2 for i in x], empenhado, w, label="Empenhado", color="#3A7FC1")
    ax.bar([i + w / 2 for i in x], pago, w, label="Pago", color="#1C3A5E")
    ax.set_xticks(x)
    ax.set_xticklabels(anos, fontsize=FONT_SIZE_SMALL)
    ax.set_ylabel("R$ milhões", fontsize=FONT_SIZE_SMALL)
    ax.tick_params(axis="y", labelsize=FONT_SIZE_SMALL)
    ax.legend(fontsize=FONT_SIZE_SMALL)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.5)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _draw_repasses_section(pdf: FPDF, data: dict) -> None:
    _section_header(pdf, "1. REPASSES AO CAPREM")
    _metric_row(
        pdf,
        [
            ("Total Empenhado", _fmt_brl(data["total_transferencias"])),
            ("Total Liquidado", _fmt_brl(data["total_liquidado"])),
            ("Total Pago", _fmt_brl(data["total_pago"])),
            ("Taxa de Pagamento", f"{data['taxa_execucao']:.1%}"),
        ],
    )
    pdf.ln(5)


def _draw_tendencia_section(pdf: FPDF, trend: pd.DataFrame) -> None:
    _section_header(pdf, "2. TENDÊNCIA HISTÓRICA")
    if trend.empty or len(trend) < 2:
        pdf.set_font("NotoSans", "I", FONT_SIZE_NORMAL)
        pdf.set_text_color(*GRAY_TEXT)
        pdf.cell(0, 6, "Dados históricos insuficientes.", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)
        return
    chart_bytes = _trend_chart_png(trend)
    pdf.image(io.BytesIO(chart_bytes), w=pdf.epw)
    pdf.ln(5)


def _draw_entidades_section(pdf: FPDF, entidades: pd.DataFrame) -> None:
    _section_header(pdf, "3. REPASSES POR ENTIDADE")
    if entidades.empty:
        pdf.set_font("NotoSans", "I", FONT_SIZE_NORMAL)
        pdf.set_text_color(*GRAY_TEXT)
        pdf.cell(0, 6, "Sem dados de entidades.", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)
        return
    with pdf.table(
        col_widths=[90, 35, 35, 20],
        headings_style=_HEADING_STYLE,
        line_height=5,
        text_align="LEFT",
        first_row_as_headings=True,
    ) as table:
        hdr = table.row()
        for col in ["Entidade", "Empenhado (R$)", "Liquidado (R$)", "Pago (R$)"]:
            hdr.cell(col)
        for _, r in entidades.iterrows():
            row = table.row(style=_ROW_WHITE)
            row.cell(str(r.get("entidade", "")))
            row.cell(_fmt_brl(float(r.get("empenhado", 0) or 0)))
            row.cell(_fmt_brl(float(r.get("liquidado", 0) or 0)))
            row.cell(_fmt_brl(float(r.get("pago", 0) or 0)))
    pdf.ln(5)


def _draw_funcoes_section(pdf: FPDF, funcoes: pd.DataFrame) -> None:
    _section_header(pdf, "4. REPASSES POR FUNÇÃO DE GOVERNO")
    if funcoes.empty:
        pdf.set_font("NotoSans", "I", FONT_SIZE_NORMAL)
        pdf.set_text_color(*GRAY_TEXT)
        pdf.cell(0, 6, "Sem dados por função.", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)
        return
    with pdf.table(
        col_widths=[50, 75, 30, 25],
        headings_style=_HEADING_STYLE,
        line_height=5,
        text_align="LEFT",
        first_row_as_headings=True,
    ) as table:
        hdr = table.row()
        for col in ["Função", "Subfunção", "Empenhado (R$)", "Pago (R$)"]:
            hdr.cell(col)
        for _, r in funcoes.iterrows():
            row = table.row(style=_ROW_WHITE)
            row.cell(str(r.get("funcao_nome", "")))
            row.cell(str(r.get("subfuncao_nome", "")))
            row.cell(_fmt_brl(float(r.get("empenhado", 0) or 0)))
            row.cell(_fmt_brl(float(r.get("pago", 0) or 0)))
    pdf.ln(5)


def _draw_natureza_section(pdf: FPDF, natureza: pd.DataFrame) -> None:
    _section_header(pdf, "5. NATUREZA DO REPASSE")
    if natureza.empty:
        pdf.set_font("NotoSans", "I", FONT_SIZE_NORMAL)
        pdf.set_text_color(*GRAY_TEXT)
        pdf.cell(0, 6, "Sem dados de natureza.", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)
        return
    with pdf.table(
        col_widths=[55, 90, 35],
        headings_style=_HEADING_STYLE,
        line_height=5,
        text_align="LEFT",
        first_row_as_headings=True,
    ) as table:
        hdr = table.row()
        for col in ["Elemento", "Natureza", "Empenhado (R$)"]:
            hdr.cell(col)
        for _, r in natureza.iterrows():
            row = table.row(style=_ROW_WHITE)
            row.cell(str(r.get("descricao", "")))
            row.cell(str(r.get("natureza", "")))
            row.cell(_fmt_brl(float(r.get("empenhado", 0) or 0)))
    pdf.ln(5)


class _CapremPDF(FPDF):
    def __init__(self, year: int, last_extracted: str) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.year = year
        self.last_extracted = last_extracted
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=20)
        self.add_font("NotoSans", "", str(FONTS_DIR / "NotoSans-Regular.ttf"))
        self.add_font("NotoSans", "B", str(FONTS_DIR / "NotoSans-Bold.ttf"))
        self.add_font("NotoSans", "I", str(FONTS_DIR / "NotoSans-Italic.ttf"))

    def header(self) -> None:
        if BRASAO_PATH.exists():
            try:
                self.image(str(BRASAO_PATH), x=15, y=10, h=20)
            except Exception:
                pass
        self.set_xy(40, 10)
        self.set_font("NotoSans", "B", FONT_SIZE_HEADER * 1.25)
        self.set_text_color(*BLUE_DARK)
        self.cell(0, 7, f"CAPREM — Caixa de Previdência Municipal — {self.year}", new_x="LMARGIN", new_y="NEXT")
        self.set_xy(40, 17)
        self.set_font("NotoSans", "", FONT_SIZE_SUBHEADER)
        self.set_text_color(*GRAY_TEXT)
        self.cell(0, 5, "Município de Porciúncula / RJ", new_x="LMARGIN", new_y="NEXT")
        self.set_xy(40, 22)
        self.set_font("NotoSans", "", FONT_SIZE_SMALL)
        self.cell(
            0,
            5,
            f"Dados extraídos do Portal da Transparência da Prefeitura Municipal de Porciúncula em: {self.last_extracted}",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.set_draw_color(*BLUE_ACCENT)
        self.set_line_width(0.4)
        self.line(15, 36, 195, 36)
        self.set_line_width(0.2)
        self.set_xy(self.l_margin, 42)
        self.set_text_color(0, 0, 0)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("NotoSans", "I", FONT_SIZE_SMALL)
        self.set_text_color(*GRAY_TEXT)
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 10, f"Gerado em: {now}   |   Página {self.page_no()}", align="C")


def generate(conn: Any, year: int) -> bytes:
    data = historia_caprem.run(conn, year)
    _raw = db.get_metadata(conn, "last_extracted_at", PortalConfig.load().slug)
    last_extracted = datetime.fromisoformat(_raw).strftime("%d/%m/%Y") if _raw else "desconhecida"

    pdf = _CapremPDF(year=year, last_extracted=last_extracted)
    pdf.add_page()

    _draw_repasses_section(pdf, data)
    _draw_tendencia_section(pdf, data["tendencia_anual"])
    _draw_entidades_section(pdf, data["entidades"])
    _draw_funcoes_section(pdf, data["funcoes"])
    _draw_natureza_section(pdf, data["natureza"])

    return bytes(pdf.output())
