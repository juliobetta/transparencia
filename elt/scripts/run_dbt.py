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

if db_url.startswith("duckdb://"):
    raw_path = db_url.replace("duckdb:///", "").replace("duckdb://", "")
    os.environ["DBT_DUCKDB_PATH"] = str(Path(raw_path).resolve())
elif "DBT_DUCKDB_PATH" in os.environ:
    os.environ["DBT_DUCKDB_PATH"] = str(Path(os.environ["DBT_DUCKDB_PATH"]).resolve())
else:
    default_duckdb = (Path(__file__).parent.parent / "transform" / "dev.duckdb").resolve()
    os.environ["DBT_DUCKDB_PATH"] = str(default_duckdb)

profiles_dir = str(Path(__file__).parent.parent / "transform")
project_dir = profiles_dir

u = urlparse(db_url) if db_url.startswith("postgresql") else None
env = {
    **os.environ,
    "DBT_HOST": (u.hostname if u and u.hostname else None) or os.environ.get("DBT_HOST", "localhost"),
    "DBT_PORT": (str(u.port) if u and u.port else None) or os.environ.get("DBT_PORT", "5544"),
    "DBT_USER": (u.username if u and u.username else None) or os.environ.get("DBT_USER", "postgres"),
    "DBT_PASSWORD": (u.password if u and u.password else None) or os.environ.get("DBT_PASSWORD", "postgres"),
    "DBT_DBNAME": (u.path.lstrip("/") if u and u.path else None) or os.environ.get("DBT_DBNAME", "postgres"),
}

cmd = [
    "dbt",
    sys.argv[1],
    "--profiles-dir",
    profiles_dir,
    "--project-dir",
    project_dir,
    *sys.argv[2:],
]
result = subprocess.run(cmd, env=env)
sys.exit(result.returncode)
