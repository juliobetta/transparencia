import os
import sys
from logging.config import fileConfig
from pathlib import Path

# Add project root to sys.path so models can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic import context  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from sqlalchemy import engine_from_config, pool  # noqa: E402

load_dotenv()

from sqlmodel import SQLModel  # noqa: E402

import models  # noqa: E402, F401 — registers all SQLModel tables in metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def render_item(type_, obj, autogen_context):
    """Replace SQLModel's AutoString with plain sa.String() in generated migrations."""
    if type_ == "type" and obj.__class__.__name__ == "AutoString":
        autogen_context.imports.add("import sqlalchemy as sa")
        return "sa.String()"
    return False


# Override sqlalchemy.url from DATABASE_URL env var if set
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_item=render_item)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
