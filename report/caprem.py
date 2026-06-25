from __future__ import annotations

import sqlite3
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import glossary
from analysis import caprem_story

REPORTS_DIR = Path("reports")
TEMPLATE_DIR = Path(__file__).parent


def generate(conn: sqlite3.Connection, year: int) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    data = caprem_story.run(conn, year)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("caprem_template.html")

    html = template.render(year=year, portal_url=glossary.PORTAL_URL, **data)

    out = REPORTS_DIR / f"caprem-{year}.html"
    out.write_text(html, encoding="utf-8")
    return out
