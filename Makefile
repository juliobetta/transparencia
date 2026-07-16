SRC = scraper.py db.py glossary.py pipeline.py analysis report dashboard elt config.py constants.py

.PHONY: install-uv install type-check lint lint/ruff lint/vulture lint/fix format format/check check test pipeline pipeline/from pipeline/only report report/compare report/saude dashboard migrate migrate/revision migrate/downgrade migrate/history migrate/grant elt/extract elt/load dbt/deps dbt/run dbt/seed dbt/test dbt/debug dbt/compile dbt/docs

# SETUP TASKS

install-uv:
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }

install: install-uv
	uv sync --group dev

# CODE QUALITY TASKS

type-check:
	uv run mypy $(SRC) --ignore-missing-imports

lint: lint/ruff

lint/fix:
	uv run ruff check --fix $(SRC)

format:
	uv run ruff format $(SRC)

format/check:
	uv run ruff format --check $(SRC)

check: lint format/check type-check

# TESTS

test:
	uv run pytest tests/ -v

# PIPELINE

pipeline/extract:
	uv run python -c "from pipeline import extract_only; extract_only(years=$(if $(YEARS),[$(YEARS)],None))"

pipeline/extract_only:
	uv run python -c "from pipeline import extract_only; extract_only(only=$(if $(ENDPOINT),'$(ENDPOINT)',None), years=$(if $(YEARS),[$(YEARS)],None))"

pipeline/load:
	uv run python -c "from pipeline import load_from_dir; load_from_dir('$(DIR)')"

# ELT — extract/load separados por portal

elt/extract:
ifndef PORTAL
	$(error PORTAL is required. Usage: make elt/extract PORTAL=porciuncula_prefeitura [YEARS="2024 2025"] [ONLY=DespesasGerais])
endif
	uv run python elt/extract/run.py --portal $(PORTAL) $(if $(YEARS),--years $(YEARS)) $(if $(ONLY),--only $(ONLY))

elt/load:
ifndef PORTAL
	$(error PORTAL is required. Usage: make elt/load PORTAL=porciuncula_prefeitura [DIR=data/raw_runs/20250101_120000])
endif
	uv run python elt/load/run.py --portal $(PORTAL) $(if $(DIR),--dir $(DIR))

# REPORTS

report:
	uv run python report/generate.py $(if $(YEAR),$(YEAR) $(MONTH))

report/saude:
ifndef YEAR
	$(error YEAR is required. Usage: make report/saude YEAR=2025)
endif
	@uv run python -c "from report.saude import generate; import db; path = generate(db.get_engine(), $(YEAR)); print(f'Report written to {path}')"

report/compare:
ifndef YEAR_A
	$(error YEAR_A is required. Usage: make report/compare YEAR_A=2023 MONTH_A_START=1 MONTH_A_END=12 YEAR_B=2024 MONTH_B_START=1 MONTH_B_END=12)
endif
ifndef YEAR_B
	$(error YEAR_B is required. Usage: make report/compare YEAR_A=2023 MONTH_A_START=1 MONTH_A_END=12 YEAR_B=2024 MONTH_B_START=1 MONTH_B_END=12)
endif
	uv run python report/compare.py $(YEAR_A) $(or $(MONTH_A_START),1) $(or $(MONTH_A_END),12) $(YEAR_B) $(or $(MONTH_B_START),1) $(or $(MONTH_B_END),12)

# MIGRATIONS

migrate:
	uv run alembic upgrade head
	$(MAKE) migrate/grant



migrate/revision:
ifndef MSG
	$(error MSG is required. Usage: make migrate/revision MSG="add some column")
endif
	uv run alembic revision --autogenerate -m "$(MSG)"

migrate/downgrade:
	uv run alembic downgrade $(or $(REV),-1)

migrate/history:
	uv run alembic history --verbose

migrate/grant:
	psql "$$DATABASE_URL" -f migrations/grant_readonly.sql

# DBT TRANSFORM

dbt/deps:
	uv run python scripts/run_dbt.py deps

dbt/seed:
	uv run python scripts/run_dbt.py seed

dbt/run:
	uv run python scripts/run_dbt.py run $(if $(SELECT),--select $(SELECT))

dbt/test:
	uv run python scripts/run_dbt.py test

dbt/debug:
	uv run python scripts/run_dbt.py debug

dbt/compile:
	uv run python scripts/run_dbt.py compile

dbt/docs:
	uv run python scripts/run_dbt.py docs generate && uv run python scripts/run_dbt.py docs serve

# DASHBOARD

dashboard:
	uv run streamlit run dashboard/app.py
