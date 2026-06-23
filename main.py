"""
Requires FlareSolverr running locally:
    docker compose up -d

Then run:
    uv run python main.py
"""
import json
from urllib.parse import urlencode
import requests

FLARESOLVERR_URL = "http://localhost:8191/v1"
BASE_URL = "https://transparencia.porciuncula.rj.gov.br/Transparencia/VersaoJson/Despesas/"

PARAMS = {
    "ConectarExercicio": "2025",
    "Listagem": "DespesasPorOrgao",
    "DiaInicioPeriodo": "01",
    "MesInicialPeriodo": "01",
    "DiaFinalPeriodo": "31",
    "MesFinalPeriodo": "12",
    "Ano": "2025",
    "Empresa": "7",
    "MostraDadosConsolidado": "False",
}


def flaresolverr_get(url: str) -> dict:
    resp = requests.post(
        FLARESOLVERR_URL,
        json={"cmd": "request.get", "url": url, "maxTimeout": 60000},
        timeout=90,
    )
    resp.raise_for_status()
    result = resp.json()
    if result["status"] != "ok":
        raise RuntimeError(f"FlareSolverr error: {result}")
    return result


def fetch(params: dict) -> dict | list:
    url = f"{BASE_URL}?{urlencode(params)}"
    print(f"Fetching: {url}")
    result = flaresolverr_get(url)
    solution = result["solution"]
    print(f"HTTP status: {solution['status']}")
    body = solution["response"]
    # FlareSolverr returns browser-rendered HTML; JSON APIs get wrapped in <pre>
    if body.lstrip().startswith("<"):
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []

            def handle_data(self, data):
                self.text.append(data)

        p = TextExtractor()
        p.feed(body)
        body = "".join(p.text).strip()
    return json.loads(body)


def main():
    import pandas as pd

    print(f"Fetching {PARAMS['Listagem']} for {PARAMS['Ano']}...")
    data = fetch(PARAMS)
    print(data)
    df = pd.DataFrame(data)
    out = f"{PARAMS['Listagem']}_{PARAMS['Ano']}.csv"
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows → {out}")
    print(df.to_string())


if __name__ == "__main__":
    main()
