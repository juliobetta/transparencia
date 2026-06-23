SRC = scraper.py db.py glossary.py pipeline.py analysis report dashboard

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

# REPORTS

report:
	uv run python report/generate.py

# DASHBOARD

dashboard:
	uv run streamlit run dashboard/app.py
