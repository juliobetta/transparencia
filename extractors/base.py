import logging
from abc import ABC
from urllib.parse import urlencode

from scraper import fetch

# TODO: Mover para config ou env variable
BASE_URL = "https://transparencia.porciuncula.rj.gov.br"


class BaseExtractor(ABC):
    def __init__(self, base_path: str, listagem: str, table: str, key_cols: list[str], extra: dict, post_process=None):
        self.base_path = base_path
        self.listagem = listagem
        self.table = table
        self.key_cols = key_cols
        self.extra = extra
        self.post_process = post_process
        self.logger = logging.getLogger(__name__)

    def get_params(self, empresa_id: int, year: int) -> dict:
        params = {
            "ConectarExercicio": str(year),
            "Listagem": self.listagem,
            "DiaInicioPeriodo": "01",
            "MesInicialPeriodo": "01",
            "DiaFinalPeriodo": "31",
            "MesFinalPeriodo": "12",
            "Ano": str(year),
            "Empresa": str(empresa_id),
            "MostraDadosConsolidado": "False",
            **self.extra,
        }

        return params

    def build_url(self, empresa_id: int, year: int) -> str:
        params = self.get_params(empresa_id, year)

        return f"{BASE_URL}{self.base_path}?{urlencode(params)}"

    def extract(self, empresa_id: int, year: int) -> list[dict]:
        url = self.build_url(empresa_id, year)
        rows = fetch(url)
        return rows
