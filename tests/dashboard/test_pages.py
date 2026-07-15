"""Smoke tests: import every dashboard page against a seeded test DB.

If a page crashes on load (e.g. KeyError on a result dict), the test fails.
Add new pages to PAGES as they are created.
"""

import importlib
import sys

import pytest

from tests.dashboard.conftest import PAGES_DIR

PAGES = [
    "visao_geral",
    "receitas",
    "despesas",
    "pessoal",
    "licitacoes",
    "orcamento",
    "saude",
    "caprem",
]


@pytest.mark.parametrize("page_name", PAGES)
def test_page_loads_without_error(page_name, page_env):  # noqa: ARG001
    # Ensure the pages directory is importable
    pages_dir = str(PAGES_DIR)
    if pages_dir not in sys.path:
        sys.path.insert(0, pages_dir)

    # Remove any cached version so the page re-executes under our patches
    sys.modules.pop(page_name, None)

    importlib.import_module(page_name)
