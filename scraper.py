import json
import logging
from html.parser import HTMLParser
import requests

FLARESOLVERR_URL = "http://localhost:8191/v1"
logger = logging.getLogger(__name__)


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text: list[str] = []

    def handle_data(self, data: str) -> None:
        self._text.append(data)

    def get_text(self) -> str:
        return "".join(self._text).strip()


def _flaresolverr_get(url: str) -> dict:
    resp = requests.post(
        FLARESOLVERR_URL,
        json={"cmd": "request.get", "url": url, "maxTimeout": 60000},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()


def fetch(url: str) -> list[dict]:
    for attempt in range(2):
        result = _flaresolverr_get(url)
        if result["status"] != "ok":
            if attempt == 0:
                logger.warning("FlareSolverr attempt 1 failed: %s — retrying", result.get("message"))
                continue
            raise RuntimeError(f"FlareSolverr error: {result}")
        break

    body = result["solution"]["response"]
    if body.lstrip().startswith("<"):
        extractor = _TextExtractor()
        extractor.feed(body)
        body = extractor.get_text()

    return json.loads(body) if body else []
