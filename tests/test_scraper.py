from unittest.mock import patch, MagicMock
import pytest
from scraper import fetch

FAKE_JSON = [{"EMPRESA": "7", "CODIGO": "01", "DESCRICAO": "SAUDE", "EMPENHADO": "1000"}]


def _mock_flare(url, **kwargs):
    m = MagicMock()
    m.raise_for_status = MagicMock()
    m.json.return_value = {
        "status": "ok",
        "solution": {
            "status": 200,
            "response": f"<html><body><pre>{__import__('json').dumps(FAKE_JSON)}</pre></body></html>",
        },
    }
    return m


def test_fetch_returns_parsed_json():
    with patch("scraper.requests.post", side_effect=_mock_flare):
        result = fetch("http://fake-url.com/?Listagem=DespesasPorOrgao")
    assert result == FAKE_JSON


def test_fetch_raises_on_flaresolverr_error():
    def bad_flare(url, **kwargs):
        m = MagicMock()
        m.raise_for_status = MagicMock()
        m.json.return_value = {"status": "error", "message": "timeout"}
        return m

    with patch("scraper.requests.post", side_effect=bad_flare):
        with pytest.raises(RuntimeError, match="FlareSolverr error"):
            fetch("http://fake-url.com/")


def test_fetch_retries_once_on_failure():
    call_count = {"n": 0}

    def flaky_flare(url, **kwargs):
        call_count["n"] += 1
        m = MagicMock()
        m.raise_for_status = MagicMock()
        if call_count["n"] == 1:
            m.json.return_value = {"status": "error", "message": "challenge"}
        else:
            m.json.return_value = {
                "status": "ok",
                "solution": {"status": 200, "response": "[]"},
            }
        return m

    with patch("scraper.requests.post", side_effect=flaky_flare):
        result = fetch("http://fake-url.com/")
    assert result == []
    assert call_count["n"] == 2
