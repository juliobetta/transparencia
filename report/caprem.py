from __future__ import annotations

from typing import Any

from report import caprem_pdf


def generate(conn: Any, year: int) -> bytes:
    return caprem_pdf.generate(conn, year)
