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
    github_url: str
    assets: dict[str, str]

    @property
    def raw_schema(self) -> str:
        return f"raw_{self.slug}"

    @property
    def orgaos_csv_path(self) -> Path:
        return Path("elt/transform/seeds") / f"seed_{self.slug}_orgaos.csv"

    def load_orgaos(self) -> dict[str, str]:
        """Returns {empresa_id: nome} from the seed CSV."""
        orgaos: dict[str, str] = {}
        with open(self.orgaos_csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                orgaos[row["empresa_id"]] = row["nome"]
        return orgaos

    @classmethod
    def load(cls, slug: str | None = None) -> "PortalConfig":
        slug = slug or os.environ["PORTAL_SLUG"]
        path = Path("portals") / f"{slug}.yml"
        data = yaml.safe_load(path.read_text())
        return cls(**data)
