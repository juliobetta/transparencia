from urllib.parse import urlencode

from .base import BASE_URL, BaseExtractor


# Post-processing helper, kept here for now as it's specific to Contratos
def _post_process_contratos(row: dict) -> dict:
    row.setdefault("numero", row.get("codigo", ""))
    proclic = row.get("proclic", "")
    row["licitacao_numero"] = proclic.split("/")[0] if proclic else ""
    row.setdefault("valor", row.get("valcon", ""))
    row.setdefault("data_inicio", row.get("vigeni", ""))
    row.setdefault("data_fim", row.get("vigenf", ""))
    return row


def _post_process_pessoal(row: dict) -> dict:
    # API sends REGISTRO; model PK uses matricula.
    if "matricula" not in row or row["matricula"] is None:
        row["matricula"] = row.get("registro")
    return row


def _post_process_despesas_extra_orcamentaria(row: dict) -> dict:
    # API sends NUMEROGUIA; model PK uses numero.
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("numeroguia") or row.get("codigo")
    return row


def _post_process_despesas_gerais(row: dict) -> dict:
    # API sends PKEMP (PK do empenho); model PK uses numero.
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("pkemp") or row.get("codigo")
    return row


def _post_process_despesas_restos_pagar(row: dict) -> dict:
    # API sends CODIGO; model PK uses numero.
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("codigo")
    return row


def _post_process_diarias(row: dict) -> dict:
    # ORDEMPAGAMENTO (payment order number) is the most unique per (ano, empresa).
    # NEMPG is the budget commitment number and repeats across many diária payments.
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("ordempagamento") or row.get("nempg")
    return row


def _post_process_emendas_cad(row: dict) -> dict:
    # API sends NUMERO_EMENDA; model PK uses numero.
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("numero_emenda") or row.get("pk_ep_emenda")
    return row


def _post_process_receita_detalhes(row: dict) -> dict:
    # API sends NLANC (número de lançamento); model PK uses codigo.
    if "codigo" not in row or row["codigo"] is None:
        row["codigo"] = row.get("nlanc") or row.get("codre")
    return row


def _post_process_transferencias(row: dict) -> dict:
    # DTLAN (data de lançamento) is unique per transfer event and the best natural key.
    if "codigo" not in row or row["codigo"] is None:
        row["codigo"] = row.get("dtlan") or f"{row.get('mes', '')}-{row.get('cnpjrecebedora', '')}"
    return row


class DespesasExtractor(BaseExtractor):
    pass


class ReceitasExtractor(BaseExtractor):
    pass


class LicitacoesExtractor(BaseExtractor):
    pass


class PessoalExtractor(BaseExtractor):
    def build_url(self, empresa_id: int, year: int) -> str:
        params = {
            "ConectarExercicio": str(year),
            "Listagem": self.listagem,
            "Empresa": str(empresa_id),
            "Ano": str(year),
            "MesFinalPeriodo": "01",
        }
        return f"{BASE_URL}{self.base_path}?{urlencode(params)}"


# Define the endpoint configurations
ENDPOINT_CONFIGS = [
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasPorOrgao",
        "despesas_por_orgao",
        ["ano", "empresa", "codigo"],
        {"MostraDadosConsolidado": "False"},
        DespesasExtractor,
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasPorUnidade",
        "despesas_por_unidade",
        ["ano", "empresa", "codigo"],
        {"MostraDadosConsolidado": "False"},
        DespesasExtractor,
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasPorFornecedor",
        "despesas_por_fornecedor",
        ["ano", "empresa", "codigo"],
        {"MostrarFornecedor": "True", "MostraDadosConsolidado": "False"},
        DespesasExtractor,
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasGerais",
        "despesas_gerais",
        ["ano", "empresa", "numero"],
        {
            "MostrarFornecedor": "True",
            "MostrarCNPJFornecedor": "True",
            "UFParaFiltroCOVID": "",
            "ApenasIDEmpenho": "False",
        },
        DespesasExtractor,
        _post_process_despesas_gerais,
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasRestosPagar",
        "despesas_restos_pagar",
        ["ano", "empresa", "numero"],
        {"ApresentaNomeFavorecido": "True", "MostraDadosConsolidado": "False"},
        DespesasExtractor,
        _post_process_despesas_restos_pagar,
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasExtraOrcamentaria",
        "despesas_extra_orcamentaria",
        ["ano", "empresa", "numero"],
        {"ApresentaNomeFavorecido": "True", "MostraDadosConsolidado": "False"},
        DespesasExtractor,
        _post_process_despesas_extra_orcamentaria,
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasporExigibilidade",
        "despesas_por_exigibilidade",
        ["ano", "empresa", "tipo"],
        {"MostraDadosConsolidado": "False"},
        DespesasExtractor,
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "Diarias",
        "diarias",
        ["ano", "empresa", "numero"],
        {"MostraDadosConsolidado": "False"},
        DespesasExtractor,
        _post_process_diarias,
    ),
    (
        "/Transparencia/VersaoJson/Receitas/",
        "ReceitaOrcamentaria",
        "receita_orcamentaria",
        ["ano", "empresa", "codigo"],
        {"MostraDadosConsolidado": "False"},
        ReceitasExtractor,
    ),
    (
        "/Transparencia/VersaoJson/Receitas/",
        "ReceitaUniao",
        "receita_uniao",
        ["ano", "empresa", "codigo"],
        {"MostraDadosConsolidado": "False"},
        ReceitasExtractor,
    ),
    (
        "/Transparencia/VersaoJson/Receitas/",
        "ReceitaEstado",
        "receita_estado",
        ["ano", "empresa", "codigo"],
        {"MostraDadosConsolidado": "False"},
        ReceitasExtractor,
    ),
    (
        "/Transparencia/VersaoJson/Receitas/",
        "ReceitaExtraOrcamentaria",
        "receita_extra_orcamentaria",
        ["ano", "empresa", "codigo"],
        {"MostraDadosConsolidado": "False"},
        ReceitasExtractor,
    ),
    (
        "/Transparencia/VersaoJson/Receitas/",
        "DetalhesReceitaOrcamentaria",
        "receita_detalhes",
        ["ano", "empresa", "codigo"],
        {"MostraDadosConsolidado": "False"},
        ReceitasExtractor,
        _post_process_receita_detalhes,
    ),
    (
        "/Transparencia/VersaoJson/LicitacoesEContratos/",
        "Licitacoes",
        "licitacoes",
        ["ano", "empresa", "numero"],
        {"MostraDadosConsolidado": "False"},
        LicitacoesExtractor,
    ),
    (
        "/Transparencia/VersaoJson/LicitacoesEContratos/",
        "Contratos",
        "contratos",
        ["ano", "empresa", "numero"],
        {"ContratosApenasPublicados": "False", "MostraDadosConsolidado": "False"},
        LicitacoesExtractor,
        _post_process_contratos,
    ),
    (
        "/Transparencia/VersaoJson/Transferencias/",
        "Transf",
        "transferencias",
        ["ano", "empresa", "codigo"],
        {"MostraDadosConsolidado": "False"},
        LicitacoesExtractor,
        _post_process_transferencias,
    ),
    (
        "/Transparencia/VersaoJson/Transferencias/",
        "EmendasImpositivasArt",
        "emendas_impositivas",
        ["ano", "empresa", "numero"],
        {"MostraDadosConsolidado": "False"},
        LicitacoesExtractor,
    ),
    (
        "/Transparencia/VersaoJson/Transferencias/",
        "CadEmendasImpositivas",
        "emendas_cad",
        ["ano", "empresa", "numero"],
        {"MostraDadosConsolidado": "False"},
        LicitacoesExtractor,
        _post_process_emendas_cad,
    ),
    (
        "/Transparencia/VersaoJson/Pessoal/",
        "Servidores",
        "pessoal",
        ["ano", "empresa", "mes", "matricula"],
        {},
        PessoalExtractor,
        _post_process_pessoal,
    ),
]
