import json
import logging
import time
from html.parser import HTMLParser
from typing import Any, cast

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


def _flaresolverr_get(url: str) -> dict[str, Any]:
    resp = requests.post(
        FLARESOLVERR_URL,
        json={"cmd": "request.get", "url": url, "maxTimeout": 60000},
        timeout=90,
    )
    resp.raise_for_status()
    result = cast(dict[str, Any], resp.json())
    if result["status"] == "error":
        # Check if it's a transient server error
        if "500" in str(result.get("message", "")):
            raise requests.HTTPError("FlareSolverr reported 500 error")
    return result


def fetch(url: str) -> list[dict[str, Any]]:
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            result = _flaresolverr_get(url)
            if result["status"] != "ok":
                raise RuntimeError(f"FlareSolverr error: {result}")

            body = result["solution"]["response"]

            # Check for HTML error pages even if HTTP status is 200
            if body.lstrip().startswith("<"):
                # It's HTML, likely an error page
                raise RuntimeError("Received HTML error page instead of JSON")

            break
        except (requests.RequestException, RuntimeError) as e:
            if attempt < max_attempts - 1:
                wait = 2**attempt
                logger.warning("Attempt %d failed: %s — retrying in %ds", attempt + 1, e, wait)
                time.sleep(wait)
                continue
            logger.error("All %d attempts failed for %s", max_attempts, url)
            return []

    # Parse JSON
    try:
        return cast(list[dict[str, Any]], json.loads(body))
    except json.JSONDecodeError:
        logger.warning("Invalid JSON from %s — skipping", url)
        return []
