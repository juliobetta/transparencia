from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, str(Path(__file__).parent.parent))

import db
import glossary
from analysis import health_story

REPORTS_DIR = Path("reports")
TEMPLATE_DIR = Path(__file__).parent


def generate(conn: sqlite3.Connection, year: int) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    data = health_story.run(conn, year)

    _raw = db.get_metadata(conn, "last_extracted_at")
    last_extracted = datetime.strptime(_raw, "%Y-%m-%d").strftime("%d/%m/%Y") if _raw else "desconhecida"

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("saude_template.html")

    # Pre-format valcon for template rendering
    if not data["bidding_gaps"].empty:
        gaps = data["bidding_gaps"].copy()
        gaps["valor_fmt"] = (
            pd.to_numeric(gaps["valcon"].astype(str).str.replace(",", "."), errors="coerce")
            .fillna(0)
            .map("{:,.0f}".format)
        )
    else:
        gaps = data["bidding_gaps"]

    if not data["splitting"].empty:
        splitting = data["splitting"].copy()
        splitting["valor_fmt"] = (
            pd.to_numeric(splitting["valcon"].astype(str).str.replace(",", "."), errors="coerce")
            .fillna(0)
            .map("{:,.0f}".format)
        )
    else:
        splitting = data["splitting"]

    # Pre-format adesao_de_ata for template rendering
    if not data["adesao_de_ata_list"].empty:
        adesao_df = data["adesao_de_ata_list"].copy()
        adesao_df["valor_fmt"] = (
            pd.to_numeric(adesao_df["total_c_valor"].astype(str).str.replace(",", "."), errors="coerce")
            .fillna(0)
            .map("{:,.0f}".format)
        )
    else:
        adesao_df = data["adesao_de_ata_list"]

    transfers_df = data["transfers_to_health"]
    html = template.render(
        year=year,
        last_extracted=last_extracted,
        portal_url=glossary.PORTAL_URL,
        emendas_total=data["emendas_total"],
        emendas=data["emendas"].to_dict("records") if not data["emendas"].empty else [],
        budget=data["budget"],
        execution_trend=data["execution_trend"].to_dict("records"),
        adesao_de_ata_count=data["adesao_de_ata_count"],
        adesao_de_ata_value=data["adesao_de_ata_value"],
        adesao_de_ata_contracts_linked_count=int(data["adesao_de_ata_list"]["has_contract"].sum()),
        adesao_de_ata_list=adesao_df.to_dict("records") if not adesao_df.empty else [],
        contracts_by_modality=data["contracts_by_modality"].to_dict("records"),
        splitting=splitting.to_dict("records") if not splitting.empty else [],
        hhi=data["hhi"],
        top_suppliers=data["top_suppliers"].to_dict("records") if not data["top_suppliers"].empty else [],
        transfers_to_health=transfers_df.to_dict("records") if not transfers_df.empty else [],
        transfers_to_health_total=data["transfers_to_health_total"],
    )

    out = REPORTS_DIR / f"saude-{year}.html"
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    conn = db.get_connection()
    from datetime import date

    path = generate(conn, date.today().year - 1)
    print(f"Report written to {path}")
