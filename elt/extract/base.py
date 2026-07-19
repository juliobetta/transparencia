import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Optional
from urllib.parse import urlencode

from scraper import fetch


@dataclass
class EndpointConfig:
    base_path: str
    listagem: str
    table: str
    key_cols: list[str]
    extra: dict[str, Any]
    extractor_cls: Any
    base_url: str = ""
    post_process: Optional[Callable] = None


class BaseExtractor(ABC):
    def __init__(
        self,
        base_path: str,
        listagem: str,
        table: str,
        key_cols: list[str],
        extra: dict,
        post_process=None,
        base_url: str = "",
    ):
        self.base_path = base_path
        self.listagem = listagem
        self.table = table
        self.key_cols = key_cols
        self.extra = extra
        self.post_process = post_process
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def get_params(self, empresa_id: str, year: int) -> dict: ...

    def build_url(self, empresa_id: str, year: int) -> str:
        params = self.get_params(empresa_id, year)
        return f"{self.base_url}{self.base_path}?{urlencode(params)}"

    def extract(self, empresa_id: str, year: int) -> list[dict]:
        url = self.build_url(empresa_id, year)
        rows = fetch(url)
        return rows
