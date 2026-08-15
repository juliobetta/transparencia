SRC = elt

.PHONY: install-uv install type-check lint lint/ruff lint/fix format format/check check test pipeline pipeline/extract pipeline/load elt/extract elt/load elt/load-csv dbt/deps dbt/run dbt/seed dbt/test dbt/debug dbt/compile dbt/docs export-parquet sync-parquet dev build test/ts db/fixture/dump db/test/restore

# SETUP TASKS

install-uv:
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }

install: install-uv
	cd elt && uv sync --group dev

# CODE QUALITY TASKS

type-check:
	uv run --project elt mypy $(SRC) --ignore-missing-imports

lint: lint/ruff

lint/ruff:
	uv run --project elt ruff check $(SRC)

lint/fix:
	uv run --project elt ruff check --fix $(SRC)

format:
	uv run --project elt ruff format $(SRC)

format/check:
	uv run --project elt ruff format --check $(SRC)

check: lint format/check type-check

# TESTS

test:
	uv run --project elt pytest -v

# PIPELINE

pipeline/extract:
	uv run --project elt python -c "from elt.core.pipeline import extract_only; extract_only(years=$(if $(YEARS),[$(YEARS)],None))"

pipeline/load:
	uv run --project elt python -c "from elt.core.pipeline import load_from_dir; load_from_dir('$(DIR)')"

# ELT — extract/load separados por portal

elt/extract:
ifndef PORTAL
	$(error PORTAL is required. Usage: make elt/extract PORTAL=porciuncula_prefeitura [YEARS="2024 2025"] [ONLY=DespesasGerais])
endif
	PYTHONPATH=. uv run --project elt python elt/extract/run.py --portal $(PORTAL) $(if $(YEARS),--years $(YEARS)) $(if $(ONLY),--only $(ONLY))

elt/load:
ifndef PORTAL
	$(error PORTAL is required. Usage: make elt/load PORTAL=porciuncula_prefeitura [DIR=data/raw_runs/20250101_120000])
endif
	PYTHONPATH=. uv run --project elt python elt/load/run.py --portal $(PORTAL) $(if $(DIR),--dir $(DIR))

elt/load-csv:
ifndef PORTAL
	$(error PORTAL is required. Usage: make elt/load-csv PORTAL=porciuncula_prefeitura)
endif
ifeq ($(PORTAL),porciuncula_prefeitura)
	PYTHONPATH=. uv run --project elt python elt/load/porciuncula_prefeitura/load_receitas_csv.py
else
	$(error No load-csv script available for portal '$(PORTAL)')
endif

# MIGRATIONS

migrate/grant:
	psql "$$DATABASE_URL" -f elt/migrations/grant_readonly.sql

# DBT TRANSFORM

dbt/deps:
	uv run --project elt python elt/scripts/run_dbt.py deps

dbt/seed:
	uv run --project elt python elt/scripts/run_dbt.py seed

dbt/run:
	uv run --project elt python elt/scripts/run_dbt.py run $(if $(SELECT),--select $(SELECT))

dbt/test:
	uv run --project elt python elt/scripts/run_dbt.py test $(if $(SELECT),--select $(SELECT))

dbt/debug:
	uv run --project elt python elt/scripts/run_dbt.py debug

dbt/compile:
	uv run --project elt python elt/scripts/run_dbt.py compile

dbt/docs:
	uv run --project elt python elt/scripts/run_dbt.py docs generate && uv run --project elt python elt/scripts/run_dbt.py docs serve

# PARQUET EXPORT

export-parquet:
	uv run --project elt python elt/export_marts_parquet.py $(if $(OUTPUT_DIR),--output-dir $(OUTPUT_DIR))

sync-parquet:
	uv run --project elt python elt/scripts/sync_parquet.py

# WEB APP (NEXT.JS)

dev:
	pnpm dev

build:
	pnpm build

test/ts:
	pnpm test

# DB TEST FIXTURE (packages/db)
# Dump SOMENTE DE SCHEMA (--schema-only) das tabelas fct_/dim_/seed_ do schema
# `public` (marts dbt) do banco de dev local (porta 5544) — sem nenhuma linha de
# dado real e sem as views de staging (que dependem do schema raw_*, fora do
# dump). Só cria as tabelas vazias; os dados usados nos testes vêm de
# packages/db/tests/fixtures/seed.ts.

db/fixture/dump:
	PGPASSWORD=postgres pg_dump -h localhost -p 5544 -U postgres -d postgres \
		--schema-only --no-owner --no-privileges --no-comments \
		-t 'public.fct_*' -t 'public.dim_*' -t 'public.seed_*' \
		| gzip -9 > packages/db/tests/fixtures/schema.sql.gz

db/test/restore:
	gunzip -c packages/db/tests/fixtures/schema.sql.gz | psql "$${DATABASE_URL:-postgresql://postgres:postgres@localhost:5545/postgres}"
