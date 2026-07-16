"""Wrapper: parses DATABASE_URL into individual env vars, then runs dbt.

Usage: uv run python scripts/run_dbt.py <dbt subcommand> [args...]
Example: uv run python scripts/run_dbt.py run --select staging
"""

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get("DATABASE_URL", "")
if not db_url:
    sys.exit("DATABASE_URL is not set")

u = urlparse(db_url)
profiles_dir = str(Path(__file__).parent.parent / "elt" / "transform")
project_dir = profiles_dir

env = {
    **os.environ,
    "DBT_HOST": u.hostname or "",
    "DBT_PORT": str(u.port or 5432),
    "DBT_USER": u.username or "",
    "DBT_PASSWORD": u.password or "",
    "DBT_DBNAME": u.path.lstrip("/"),
}

cmd = [
    "dbt",
    "--profiles-dir",
    profiles_dir,
    "--project-dir",
    project_dir,
    *sys.argv[1:],
]
result = subprocess.run(cmd, env=env)
sys.exit(result.returncode)
