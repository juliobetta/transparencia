from __future__ import annotations

import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import db
import glossary
from analysis import (
    bidding_gaps,
    budget_execution,
    payroll_vs_services,
    revenue_sources,
    supplier_concentration,
    yoy_trends,
)
from db import get_metadata

REPORTS_DIR = Path("reports")
TEMPLATE_DIR = Path(__file__).parent


def generate(conn: sqlite3.Connection, year: int, month: int) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)

    budget = budget_execution.run(conn, year)
    supplier = supplier_concentration.run(conn, year)  # dict with top10/hhi/dominante
    bidding = bidding_gaps.run(conn, year)
    # Pre-filter for template — Jinja2 can't do pandas boolean indexing
    bidding_acima = bidding[bidding["acima_limite"]].to_dict("records")
    bidding_saude = bidding[bidding["acima_limite"] & bidding["orgao_saude"]]
    revenue = revenue_sources.run(conn, list(range(2022, year + 1)))
    payroll = payroll_vs_services.run(conn, list(range(2022, year + 1)))
    trends = yoy_trends.run(conn, list(range(2022, year + 1)))

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("template.html")
    _raw = get_metadata(conn, "last_extracted_at")
    last_extracted = datetime.strptime(_raw, "%Y-%m-%d").strftime("%m/%d/%Y") if _raw else "desconhecida"

    html = template.render(
        year=year,
        month=month,
        last_extracted=last_extracted,
        portal_url=glossary.PORTAL_URL,
        glossario=glossary.TERMS,
        budget=budget,
        supplier=supplier,  # Jinja2 dot-notation works on dicts natively
        bidding=bidding,
        bidding_acima=bidding_acima,
        bidding_saude_count=len(bidding_saude),
        revenue=revenue,
        payroll=payroll,
        trends=trends,
    )

    out = REPORTS_DIR / f"{year}-{month:02d}.html"
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    import sys

    today = date.today()
    args = sys.argv[1:]
    if len(args) == 2:
        year, month = int(args[0]), int(args[1])
    elif len(args) == 0:
        year, month = today.year, today.month
    else:
        print("Usage: generate.py [YEAR MONTH]", file=sys.stderr)
        sys.exit(1)

    conn = db.get_connection()
    path = generate(conn, year, month)
    print(f"Report written to {path}")
    conn.close()
