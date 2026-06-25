from urllib.parse import urlencode

from .base import BASE_URL, BaseExtractor


# Post-processing helper, kept here for now as it's specific to Contratos
def _post_process_contratos(row: dict) -> dict:
    row.setdefault("numero", row.get("codigo", ""))
    proclic = row.get("proclic", "")
    row["licitacao_numero"] = proclic.split("/")[0] if proclic else ""
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
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasRestosPagar",
        "despesas_restos_pagar",
        ["ano", "empresa", "numero"],
        {"ApresentaNomeFavorecido": "True", "MostraDadosConsolidado": "False"},
        DespesasExtractor,
    ),
    (
        "/Transparencia/VersaoJson/Despesas/",
        "DespesasExtraOrcamentaria",
        "despesas_extra_orcamentaria",
        ["ano", "empresa", "numero"],
        {"ApresentaNomeFavorecido": "True", "MostraDadosConsolidado": "False"},
        DespesasExtractor,
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
    ),
    (
        "/Transparencia/VersaoJson/Pessoal/",
        "Servidores",
        "pessoal",
        ["ano", "empresa", "mes", "matricula"],
        {},
        PessoalExtractor,
    ),
]
