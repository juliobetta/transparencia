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
FONTS_DIR = ASSETS_DIR / "fonts"

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
    pdf.set_font("NotoSans", "B", 11)
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
        pdf.set_font("NotoSans", "", 8)
        pdf.set_text_color(*GRAY_TEXT)
        pdf.cell(w, 6, label, fill=True, new_x="RIGHT", new_y="TOP")
        pdf.set_xy(x, start_y + 6)
        pdf.set_font("NotoSans", "B", 12)
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
        pdf.set_font("NotoSans", "", 9)
        pdf.multi_cell(0, 6, "[!] Taxa de execução abaixo de 70% para ano encerrado.", fill=True)
        pdf.ln(3)
    if not budget_trend.empty and len(budget_trend) >= 2:
        chart_bytes = _budget_chart_png(budget_trend)
        pdf.image(io.BytesIO(chart_bytes), w=pdf.epw)
    pdf.ln(5)


def _draw_emendas_section(pdf: FPDF, emendas: pd.DataFrame, emendas_total: float) -> None:
    _section_header(pdf, "2. EMENDAS PARLAMENTARES")
    if emendas_total <= 0:
        pdf.set_font("NotoSans", "I", 9)
        pdf.cell(0, 6, "Sem emendas parlamentares registradas.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        return

    _metric_row(pdf, [("Total Recebido (Valor Autorizado)", _fmt_brl(emendas_total))])

    if emendas.empty:
        pdf.ln(2)
        return

    headings_style = FontFace(fill_color=BLUE_MID, color=(255, 255, 255), emphasis="BOLD", size_pt=9)
    with pdf.table(
        col_widths=[65, 65, 27, 23],
        headings_style=headings_style,
        line_height=5,
        text_align="LEFT",
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
    _metric_row(pdf, [("Índice HHI (concentração de mercado)", f"{hhi:,.0f} — {hhi_label}")])

    if top_suppliers.empty:
        pdf.set_font("NotoSans", "I", 9)
        pdf.cell(0, 6, "Sem dados de fornecedores.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        return

    headings_style = FontFace(fill_color=BLUE_MID, color=(255, 255, 255), emphasis="BOLD", size_pt=9)
    with pdf.table(
        col_widths=[100, 45, 35],
        headings_style=headings_style,
        line_height=5,
        text_align="LEFT",
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
    _truncation_note(pdf, len(top_suppliers))
    pdf.ln(5)


def _truncation_note(pdf: FPDF, total: int, shown: int = 10) -> None:
    if total > shown:
        pdf.set_font("NotoSans", "I", 8)
        pdf.set_text_color(*GRAY_TEXT)
        pdf.cell(0, 5, f"Exibindo os {shown} primeiros de {total} registros.", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)


def _valcon_float(r: pd.Series) -> float:
    try:
        return float(str(r.get("valcon", 0)).replace(",", "."))
    except (ValueError, TypeError):
        return 0.0


def _gaps_table(pdf: FPDF, rows: pd.DataFrame, cols: list[str], widths: list[float]) -> None:
    headings_style = FontFace(fill_color=BLUE_MID, color=(255, 255, 255), emphasis="BOLD", size_pt=9)
    with pdf.table(
        col_widths=widths, headings_style=headings_style, line_height=5, text_align="LEFT", first_row_as_headings=True
    ) as t:
        hdr = t.row()
        for col in cols:
            hdr.cell(col)
        for _, r in rows.head(10).iterrows():
            row = t.row()
            row.cell(str(r.get("fornecedor", "")))
            row.cell(str(r.get("objeto", "")))
            row.cell(str(r.get("modali", "") or ""))
            row.cell(_fmt_brl(_valcon_float(r)))
    _truncation_note(pdf, len(rows))


def _draw_alertas_section(
    pdf: FPDF,
    bidding_gaps: pd.DataFrame,
    splitting: pd.DataFrame,
    adesao_list: pd.DataFrame,  # noqa: ARG001
    adesao_value: float,
    adesao_count: int,
) -> None:
    _section_header(pdf, "4. ALERTAS & IRREGULARIDADES")

    irregular = bidding_gaps[~bidding_gaps["is_legally_exempt"]] if not bidding_gaps.empty else pd.DataFrame()
    exempt = bidding_gaps[bidding_gaps["is_legally_exempt"]] if not bidding_gaps.empty else pd.DataFrame()

    gaps_count = len(irregular)
    splitting_count = splitting["fornecedor"].nunique() if not splitting.empty else 0

    alerts = [
        (gaps_count, f"Contratos potencialmente irregulares (sem licitação, acima do limite): {gaps_count}"),
        (splitting_count, f"Fornecedores com possível fracionamento: {splitting_count}"),
        (adesao_count, f"Adesão de ata (carona): {adesao_count} contratos — {_fmt_brl(adesao_value)}"),
    ]

    has_alert = any(count > 0 for count, _ in alerts)
    if not has_alert and exempt.empty:
        pdf.set_fill_color(212, 237, 218)
        pdf.set_font("NotoSans", "", 9)
        pdf.multi_cell(0, 6, "Nenhum alerta identificado para o período.", fill=True)
        pdf.ln(4)
        return

    for count, msg in alerts:
        if count > 0:
            pdf.set_fill_color(*WARN_BG)
            pdf.set_font("NotoSans", "", 9)
            pdf.multi_cell(0, 6, f"[!]  {msg}", fill=True)
            pdf.ln(2)

    _COL_HEADERS = ["Fornecedor", "Objeto", "Modalidade", "Valor (R$)"]
    _COL_WIDTHS = [55, 65, 35, 25]

    if not irregular.empty:
        pdf.ln(2)
        pdf.set_font("NotoSans", "B", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(
            0,
            5,
            "Contratos potencialmente irregulares (acima do limite sem fundamento legal):",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(1)
        _gaps_table(pdf, irregular, _COL_HEADERS, _COL_WIDTHS)

    if not exempt.empty:
        pdf.ln(3)
        pdf.set_font("NotoSans", "B", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(
            0,
            5,
            "Contratos acima do limite com fundamento legal (Inexigibilidade — Art. 74):",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(1)
        _gaps_table(pdf, exempt, _COL_HEADERS, _COL_WIDTHS)

    pdf.ln(5)


def _draw_medicamentos_section(pdf: FPDF, pharma_empenhos: dict, pharma_judicial: dict) -> None:
    _section_header(pdf, "5. MEDICAMENTOS & INSUMOS FARMACÊUTICOS")
    _metric_row(
        pdf,
        [
            ("Total Empenhado (Material Farmacêutico)", _fmt_brl(pharma_empenhos.get("total", 0.0))),
            ("Total em Mandados Judiciais", _fmt_brl(pharma_judicial.get("total", 0.0))),
        ],
    )

    detail: pd.DataFrame = pharma_empenhos.get("detail", pd.DataFrame())
    if detail.empty:
        pdf.set_font("NotoSans", "I", 9)
        pdf.cell(0, 6, "Sem dados de insumos farmacêuticos.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        return

    pdf.set_font("NotoSans", "B", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, "Top fornecedores de insumos farmacêuticos:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    headings_style = FontFace(fill_color=BLUE_MID, color=(255, 255, 255), emphasis="BOLD", size_pt=9)
    with pdf.table(
        col_widths=[70, 80, 30],
        headings_style=headings_style,
        line_height=5,
        text_align="LEFT",
        first_row_as_headings=True,
    ) as table:
        hdr = table.row()
        for col in ["Fornecedor", "Produto", "Total (R$)"]:
            hdr.cell(col)
        for _, r in detail.head(10).iterrows():
            row = table.row()
            row.cell(str(r.get("fornecedor", "")))
            row.cell(str(r.get("descricao", "")))
            row.cell(_fmt_brl(float(r.get("total", 0) or 0)))
    _truncation_note(pdf, len(detail))
    pdf.ln(5)


class _SaudePDF(FPDF):
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
        self.set_font("NotoSans", "B", 14)
        self.set_text_color(*BLUE_DARK)
        self.cell(0, 7, f"Fundo Municipal de Saúde — {self.year}", new_x="LMARGIN", new_y="NEXT")
        self.set_xy(40, 17)
        self.set_font("NotoSans", "", 10)
        self.set_text_color(*GRAY_TEXT)
        self.cell(0, 5, "Município de Porciúncula / RJ", new_x="LMARGIN", new_y="NEXT")
        self.set_xy(40, 22)
        self.set_font("NotoSans", "", 9)
        self.cell(0, 5, f"Dados extraídos em: {self.last_extracted}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*BLUE_DARK)
        self.line(15, 36, 195, 36)
        self.set_xy(self.l_margin, 42)
        self.set_text_color(0, 0, 0)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("NotoSans", "I", 8)
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
    _draw_alertas_section(
        pdf,
        data["bidding_gaps"],
        data["splitting"],
        data["adesao_de_ata_list"],
        data["adesao_de_ata_value"],
        data["adesao_de_ata_count"],
    )
    _draw_medicamentos_section(pdf, data["pharma_empenhos"], data["pharma_judicial"])

    return bytes(pdf.output())
