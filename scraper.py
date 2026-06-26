import json
import logging
import time
from html.parser import HTMLParser
from typing import Any, cast

import requests

FLARESOLVERR_URL = "http://localhost:8191/v1"
logger = logging.getLogger(__name__)


class FlareSolverrClient:
    """Encapsulates interaction with local FlareSolverr proxy server."""

    class _TextExtractor(HTMLParser):
        """Internal HTML Parser to strip browser-rendered wraps from FlareSolverr responses."""

        def __init__(self) -> None:
            super().__init__()
            self._text: list[str] = []

        def handle_data(self, data: str) -> None:
            self._text.append(data)

        def get_text(self) -> str:
            return "".join(self._text).strip()

    @staticmethod
    def _post_request(url: str) -> dict[str, Any]:
        """Performs a synchronous HTTP post request to the FlareSolverr instance."""
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

    @classmethod
    def fetch(cls, url: str) -> list[dict[str, Any]]:
        """Fetches a URL using FlareSolverr, supporting exponential retries and body validation."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                result = cls._post_request(url)
                if result["status"] != "ok":
                    raise RuntimeError(f"FlareSolverr error: {result}")

                body = result["solution"]["response"]

                # FlareSolverr returns browser-rendered HTML; JSON APIs get wrapped in <pre>
                # Extract the raw text from HTML wrapper if it's there
                if body.lstrip().startswith("<"):
                    extractor = cls._TextExtractor()
                    extractor.feed(body)
                    extracted_body = extractor.get_text()
                else:
                    extracted_body = body

                # If the extracted text is empty or doesn't look like JSON (starts with [ or {),
                # it's likely an HTML error page or server-side exception page.
                stripped_body = extracted_body.lstrip()
                if not stripped_body or not (stripped_body.startswith("[") or stripped_body.startswith("{")):
                    raise RuntimeError(
                        f"Response is not valid JSON (likely HTML error page): {extracted_body[:100]}..."
                    )

                body = extracted_body
                break
            except (requests.RequestException, RuntimeError) as e:
                if attempt < max_attempts - 1:
                    wait = 2**attempt
                    logger.warning("Attempt %d failed: %s — retrying in %ds", attempt + 1, e, wait)
                    time.sleep(wait)
                    continue
                logger.error("All %d attempts failed for %s", max_attempts, url)
                raise

        # Parse JSON
        try:
            return cast(list[dict[str, Any]], json.loads(body))
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from %s — skipping", url)
            return []


def fetch(url: str) -> list[dict[str, Any]]:
    """Backwards-compatible API wrapper for FlareSolverrClient.fetch()"""
    return FlareSolverrClient.fetch(url)
