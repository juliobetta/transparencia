SRC = scraper.py db.py glossary.py pipeline.py analysis report dashboard

.PHONY: install-uv install type-check lint lint/ruff lint/vulture lint/fix format format/check check test pipeline pipeline/from pipeline/only report report/compare dashboard

# SETUP TASKS

install-uv:
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }

install: install-uv
	uv sync --group dev

# CODE QUALITY TASKS

type-check:
	uv run mypy $(SRC) --ignore-missing-imports

lint: lint/ruff lint/vulture

lint/ruff:
	uv run ruff check $(SRC)

lint/vulture:
	uv run vulture $(SRC)

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

pipeline:
	uv run python pipeline.py

pipeline/from:
	uv run python -c "from pipeline import run; run(start_from='$(FROM)', years=$(if $(YEARS),[$(YEARS)],None))"

pipeline/only:
	uv run python -c "from pipeline import run; run(only='$(ENDPOINT)', years=$(if $(YEARS),[$(YEARS)],None))"

# REPORTS

report:
	uv run python report/generate.py $(if $(YEAR),$(YEAR) $(MONTH))

report/compare:
ifndef YEAR_A
	$(error YEAR_A is required. Usage: make report/compare YEAR_A=2023 MONTH_A_START=1 MONTH_A_END=12 YEAR_B=2024 MONTH_B_START=1 MONTH_B_END=12)
endif
ifndef YEAR_B
	$(error YEAR_B is required. Usage: make report/compare YEAR_A=2023 MONTH_A_START=1 MONTH_A_END=12 YEAR_B=2024 MONTH_B_START=1 MONTH_B_END=12)
endif
	uv run python report/compare.py $(YEAR_A) $(or $(MONTH_A_START),1) $(or $(MONTH_A_END),12) $(YEAR_B) $(or $(MONTH_B_START),1) $(or $(MONTH_B_END),12)

# DASHBOARD

dashboard:
	uv run streamlit run dashboard/app.py
