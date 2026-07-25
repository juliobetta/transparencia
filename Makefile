SRC = elt

.PHONY: install-uv install type-check lint lint/ruff lint/fix format format/check check test pipeline pipeline/extract pipeline/load elt/extract elt/load elt/load-csv dbt/deps dbt/run dbt/seed dbt/test dbt/debug dbt/compile dbt/docs dev build test/ts

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
	PYTHONPATH=elt uv run --project elt python elt/extract/run.py --portal $(PORTAL) $(if $(YEARS),--years $(YEARS)) $(if $(ONLY),--only $(ONLY))

elt/load:
ifndef PORTAL
	$(error PORTAL is required. Usage: make elt/load PORTAL=porciuncula_prefeitura [DIR=data/raw_runs/20250101_120000])
endif
	PYTHONPATH=elt uv run --project elt python elt/load/run.py --portal $(PORTAL) $(if $(DIR),--dir $(DIR))

elt/load-csv:
ifndef PORTAL
	$(error PORTAL is required. Usage: make elt/load-csv PORTAL=porciuncula_prefeitura)
endif
ifeq ($(PORTAL),porciuncula_prefeitura)
	PYTHONPATH=elt uv run --project elt python elt/load/porciuncula_prefeitura/load_receitas_csv.py
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
	uv run --project elt python elt/scripts/run_dbt.py test

dbt/debug:
	uv run --project elt python elt/scripts/run_dbt.py debug

dbt/compile:
	uv run --project elt python elt/scripts/run_dbt.py compile

dbt/docs:
	uv run --project elt python elt/scripts/run_dbt.py docs generate && uv run --project elt python elt/scripts/run_dbt.py docs serve

# WEB APP (NEXT.JS)

dev:
	pnpm dev

build:
	pnpm build

test/ts:
	pnpm test
