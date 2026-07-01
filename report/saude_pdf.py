from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib
from fpdf import FPDF

matplotlib.use("Agg")

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
    health_story.run(conn, year)
    _raw = db.get_metadata(conn, "last_extracted_at")
    last_extracted = datetime.strptime(_raw, "%Y-%m-%d").strftime("%d/%m/%Y") if _raw else "desconhecida"

    pdf = _SaudePDF(year=year, last_extracted=last_extracted)
    pdf.add_page()

    return bytes(pdf.output())
