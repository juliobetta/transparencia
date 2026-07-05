from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from jinja2 import Environment, FileSystemLoader

import db
import glossary
from analysis.comparison import PeriodSpec, run

REPORTS_DIR = Path(__file__).parent.parent / "reports"
TEMPLATE_DIR = Path(__file__).parent


def generate(conn, spec_a: PeriodSpec, spec_b: PeriodSpec) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    result = run(conn, spec_a, spec_b)
    _raw = db.get_metadata(conn, "last_extracted_at")
    last_extracted = datetime.strptime(_raw, "%Y-%m-%d").strftime("%m/%d/%Y") if _raw else "desconhecida"

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("compare_template.html")
    html = template.render(
        spec_a=spec_a,
        spec_b=spec_b,
        last_extracted=last_extracted,
        portal_url=glossary.PORTAL_URL,
        glossario=glossary.TERMS,
        result=result,
    )

    slug_a = f"{spec_a.year}-{spec_a.mes_inicio:02d}-{spec_a.mes_fim:02d}"
    slug_b = f"{spec_b.year}-{spec_b.mes_inicio:02d}-{spec_b.mes_fim:02d}"
    out = REPORTS_DIR / f"compare_{slug_a}_vs_{slug_b}.html"
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 6:
        print(
            "Usage: compare.py YEAR_A MONTH_A_START MONTH_A_END YEAR_B MONTH_B_START MONTH_B_END",
            file=sys.stderr,
        )
        sys.exit(1)

    spec_a = PeriodSpec(year=int(args[0]), mes_inicio=int(args[1]), mes_fim=int(args[2]))
    spec_b = PeriodSpec(year=int(args[3]), mes_inicio=int(args[4]), mes_fim=int(args[5]))

    engine = db.get_engine()
    path = generate(engine, spec_a, spec_b)
    print(f"Report written to {path}")
