import json
import logging
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from db import create_tables, get_connection, upsert
from scraper import fetch

RAW_DIR = Path("data/raw")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_HOST = "https://transparencia.porciuncula.rj.gov.br"

ENTITIES = {
    7: "Prefeitura Municipal",
    2: "Fundo Municipal de Saúde",
    3: "Fundo Municipal de Assistência Social",
    8: "Fundo Municipal de Educação",
    9: "Fundo Municipal de Defesa Ambiental",
    10: "Fundo de Solidariedade — FUNDESOL",
}

ENDPOINTS = [
    ("/Transparencia/VersaoJson/Despesas/", "DespesasPorOrgao", "despesas_por_orgao", ["ano", "empresa", "codigo"], {}),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasPorUnidade",
        "despesas_por_unidade",
        ["ano", "empresa", "codigo"],
        {},
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasPorFornecedor",
        "despesas_por_fornecedor",
        ["ano", "empresa", "codigo"],
        {},
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasGerais",
        "despesas_gerais",
        ["ano", "empresa", "numero"],
        {"MostrarFornecedor": "True", "MostrarCNPJFornecedor": "True"},
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasRestosPagar",
        "despesas_restos_pagar",
        ["ano", "empresa", "numero"],
        {"ApresentaNomeFavorecido": "True"},
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasExtraOrcamentaria",
        "despesas_extra_orcamentaria",
        ["ano", "empresa", "numero"],
        {"ApresentaNomeFavorecido": "True"},
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasporExigibilidade",
        "despesas_por_exigibilidade",
        ["ano", "empresa", "tipo"],
        {},
    ),
    ("/Transparencia/VersaoJson/Despesas/", "Diarias", "diarias", ["ano", "empresa", "numero"], {}),
    (
        "/Transparencia/VersaoJson/Receitas/",
        "ReceitaOrcamentaria",
        "receita_orcamentaria",
        ["ano", "empresa", "codigo"],
        {},
    ),
    ("/Transparencia/VersaoJson/Receitas/", "ReceitaUniao", "receita_uniao", ["ano", "empresa", "codigo"], {}),
    ("/Transparencia/VersaoJson/Receitas/", "ReceitaEstado", "receita_estado", ["ano", "empresa", "codigo"], {}),
    (
        "/Transparencia/VersaoJson/Receitas/",
        "ReceitaExtraOrcamentaria",
        "receita_extra_orcamentaria",
        ["ano", "empresa", "codigo"],
        {},
    ),
    (
        "/Transparencia/VersaoJson/Receitas/",
        "DetalhesReceitaOrcamentaria",
        "receita_detalhes",
        ["ano", "empresa", "codigo"],
        {},
    ),
    ("/Transparencia/VersaoJson/LicitacoesEContratos/", "Licitacoes", "licitacoes", ["ano", "empresa", "numero"], {}),
    (
        "/Transparencia/VersaoJson/LicitacoesEContratos/",
        "Contratos",
        "contratos",
        ["ano", "empresa", "numero"],
        {"ContratosApenasPublicados": "False"},
    ),
    ("/Transparencia/VersaoJson/Transferencias/", "Transf", "transferencias", ["ano", "empresa", "codigo"], {}),
    (
        "/Transparencia/VersaoJson/Transferencias/",
        "EmendasImpositivasArt",
        "emendas_impositivas",
        ["ano", "empresa", "numero"],
        {},
    ),
    (
        "/Transparencia/VersaoJson/Transferencias/",
        "CadEmendasImpositivas",
        "emendas_cad",
        ["ano", "empresa", "numero"],
        {},
    ),
    ("/Transparencia/VersaoJson/Pessoal/", "Servidores", "pessoal", ["ano", "empresa", "mes", "matricula"], {}),
]

START_YEAR = 2022


def _build_url(path: str, listagem: str, empresa_id: int, year: int, extra: dict) -> str:
    params = {
        "ConectarExercicio": str(year),
        "Listagem": listagem,
        "DiaInicioPeriodo": "01",
        "MesInicialPeriodo": "01",
        "DiaFinalPeriodo": "31",
        "MesFinalPeriodo": "12",
        "Ano": str(year),
        "Empresa": str(empresa_id),
        "MostraDadosConsolidado": "False",
        **extra,
    }
    return f"{BASE_HOST}{path}?{urlencode(params)}"


def _normalize(rows: list[dict], ano: int, empresa: str) -> list[dict]:
    out = []
    for r in rows:
        normalised = {k.lower(): v for k, v in r.items()}
        normalised.setdefault("ano", ano)
        normalised.setdefault("empresa", empresa)
        out.append(normalised)
    return out


def run(years: list[int] | None = None, start_from: str | None = None, only: str | None = None) -> None:
    if years is None:
        years = list(range(START_YEAR, date.today().year + 1))

    conn = get_connection()
    create_tables(conn)

    valid = [e[1] for e in ENDPOINTS]
    endpoints = ENDPOINTS
    if only:
        if only not in valid:
            raise ValueError(f"Unknown listagem: {only!r}. Valid values: {valid}")
        endpoints = [e for e in ENDPOINTS if e[1] == only]
    elif start_from:
        if start_from not in valid:
            raise ValueError(f"Unknown listagem: {start_from!r}. Valid values: {valid}")
        idx = next(i for i, e in enumerate(ENDPOINTS) if e[1] == start_from)
        endpoints = ENDPOINTS[idx:]

    total = len(endpoints) * len(ENTITIES) * len(years)
    done = 0

    for path, listagem, table, key_cols, extra in endpoints:
        for empresa_id, empresa_name in ENTITIES.items():
            for year in years:
                url = _build_url(path, listagem, empresa_id, year, extra)
                try:
                    rows = fetch(url)
                    raw_path = RAW_DIR / table / f"{empresa_id}_{year}.json"
                    raw_path.parent.mkdir(parents=True, exist_ok=True)
                    raw_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
                    normalised = _normalize(rows, year, str(empresa_id))
                    count = upsert(conn, table, normalised, key_cols)
                    logger.info("[%d/%d] %s / %s / %d → %d rows", done + 1, total, listagem, empresa_name, year, count)
                except Exception as exc:
                    logger.warning("SKIP %s / %s / %d: %s", listagem, empresa_name, year, exc)
                done += 1

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    run()
