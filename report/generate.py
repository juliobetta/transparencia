from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, str(Path(__file__).parent.parent))

import constants
import db
import glossary
from analysis import (
    adesao_de_ata,
    concentracao_fornecedores,
    execucao_orcamentaria,
    folha_vs_servicos,
    fontes_receita,
    licitacao_gaps,
    tendencias_anuais,
)
from analysis.constants import THRESHOLD_COMPRAS_SERVICOS, THRESHOLD_OBRAS_ENGENHARIA, THRESHOLD_VEICULOS
from config import PortalConfig
from dashboard.shared import ANO_INICIAL
from db import get_metadata

REPORTS_DIR = Path("reports")
TEMPLATE_DIR = Path(__file__).parent


def generate(engine, year: int, month: int) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)

    budget = execucao_orcamentaria.run(engine, year)
    supplier = concentracao_fornecedores.run(engine, year)
    bidding = licitacao_gaps.run(engine, year)
    adesao = adesao_de_ata.run(engine, year, ["2"])
    bidding_acima = licitacao_gaps.filter_above_limit(bidding).to_dict("records")
    bidding_saude = licitacao_gaps.filter_above_limit_health(bidding)
    revenue = fontes_receita.run(engine, list(range(ANO_INICIAL, year + 1)))
    payroll = folha_vs_servicos.run(engine, list(range(ANO_INICIAL, year + 1)))
    trends = tendencias_anuais.run(engine, list(range(ANO_INICIAL, year + 1)))

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("template.html")
    _raw = get_metadata(engine, "last_extracted_at", PortalConfig.load().slug)
    last_extracted = datetime.strptime(_raw, "%Y-%m-%d").strftime("%m/%d/%Y") if _raw else "desconhecida"

    html = template.render(
        year=year,
        month=month,
        last_extracted=last_extracted,
        portal_url=constants.PORTAL_URL,
        glossario=glossary.TERMS,
        budget=budget,
        supplier=supplier,
        bidding=bidding,
        bidding_acima=bidding_acima,
        bidding_saude_count=len(bidding_saude),
        adesao=adesao,
        revenue=revenue,
        payroll=payroll,
        trends=trends,
        threshold_compras=THRESHOLD_COMPRAS_SERVICOS,
        threshold_obras=THRESHOLD_OBRAS_ENGENHARIA,
        threshold_veiculos=THRESHOLD_VEICULOS,
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

    engine = db.get_engine()
    path = generate(engine, year, month)
    print(f"Report written to {path}")
