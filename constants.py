import os
from pathlib import Path

import yaml

_slug = os.environ.get("PORTAL_SLUG", "porciuncula_prefeitura")
_data: dict = yaml.safe_load((Path(__file__).parent / "portals" / f"{_slug}.yml").read_text())

PORTAL_URL: str = _data["portal_url"]
GITHUB_URL: str = _data["github_url"]
