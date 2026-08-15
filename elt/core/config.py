import csv
import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class PortalConfig:
    slug: str
    display_name: str
    uf: str
    portal_url: str
    base_host: str
    cidade_clean: str
    ano_inicial: int
    empresa_padrao: str
    assets: dict[str, str]
    github_url: str | None = None

    @property
    def raw_schema(self) -> str:
        return f"raw_{self.slug}"

    @property
    def orgaos_csv_path(self) -> Path:
        return Path(__file__).parent.parent / "transform" / "seeds" / f"seed_{self.slug}_orgaos.csv"

    def load_orgaos(self) -> dict[str, str]:
        """Returns {empresa_id: nome} from the seed CSV."""
        orgaos: dict[str, str] = {}
        with open(self.orgaos_csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                orgaos[row["empresa_id"]] = row["nome"]
        return orgaos

    @classmethod
    def load(cls, slug: str | None = None) -> "PortalConfig":
        # Default hardcoded until multi-portal support is added (URL/host-based routing)
        slug = slug or os.environ.get("PORTAL_SLUG", "porciuncula_prefeitura")
        path = Path(__file__).parent.parent / "portals" / f"{slug}.yml"
        data = yaml.safe_load(path.read_text())
        return cls(**data)


def get_source_columns(table_name: str, slug: str = "porciuncula_prefeitura") -> list[str]:
    """Returns declared column names from _sources.yml for the given table."""
    sources_yml = Path(__file__).parent.parent / "transform" / "models" / "staging" / slug / "_sources.yml"
    if not sources_yml.exists():
        return []
    data = yaml.safe_load(sources_yml.read_text())
    for src in data.get("sources", []):
        for tbl in src.get("tables", []):
            if tbl.get("name") == table_name:
                return [c["name"] for c in tbl.get("columns", [])]
    return []
