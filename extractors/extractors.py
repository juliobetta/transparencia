from urllib.parse import urlencode

from utils.masking import is_cpf, mask_cpf, mask_name

from .base import BASE_URL, BaseExtractor


# Auxiliar de pós-processamento, mantido aqui por enquanto, pois é específico para Contratos
def _post_process_contratos(row: dict) -> dict:
    row.setdefault("numero", row.get("codigo", ""))
    proclic = row.get("proclic", "")
    row["licitacao_numero"] = proclic.split("/")[0] if proclic else ""
    row.setdefault("valor", row.get("valcon", ""))
    row.setdefault("data_inicio", row.get("vigeni", ""))
    row.setdefault("data_fim", row.get("vigenf", ""))
    return row


def _post_process_pessoal(row: dict) -> dict:
    # A API envia REGISTRO; a PK do modelo usa matricula.
    if "matricula" not in row or row["matricula"] is None:
        row["matricula"] = row.get("registro")
    return row


def _post_process_fornecedor(row: dict) -> dict:
    """Aplica anonimização se o campo INSMF for um CPF."""
    documento = row.get("INSMF", "")
    if is_cpf(documento):
        row["INSMF"] = mask_cpf(documento)
        if "DESCRICAO" in row:
            row["DESCRICAO"] = mask_name(row["DESCRICAO"])
    return row


def _post_process_despesas_extra_orcamentaria(row: dict) -> dict:
    # A API envia NUMEROGUIA; a PK do modelo usa numero.
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("numeroguia") or row.get("codigo")
    return row


def _post_process_despesas_gerais(row: dict) -> dict:
    # A API envia PKEMP (PK do empenho); a PK do modelo usa numero.
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("pkemp") or row.get("codigo")
    return row


def _post_process_despesas_restos_pagar(row: dict) -> dict:
    # A API envia CODIGO; a PK do modelo usa numero.
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("codigo")
    return row


def _post_process_diarias(row: dict) -> dict:
    # ORDEMPAGAMENTO (número da ordem de pagamento) é o mais exclusivo por (ano, empresa).
    # NEMPG é o número do empenho orçamentário e se repete em muitos pagamentos de diárias.
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("ordempagamento") or row.get("nempg")
    return row


def _post_process_emendas_cad(row: dict) -> dict:
    # A API envia NUMERO_EMENDA; a PK do modelo usa numero.
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("numero_emenda") or row.get("pk_ep_emenda")
    return row


def _post_process_receita_detalhes(row: dict) -> dict:
    # A API envia NLANC (número de lançamento); a PK do modelo usa codigo.
    if "codigo" not in row or row["codigo"] is None:
        row["codigo"] = row.get("nlanc") or row.get("codre")
    return row


def _post_process_transferencias(row: dict) -> dict:
    # DTLAN (data de lançamento) é exclusiva por evento de transferência e a melhor chave natural.
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


# Define as configurações dos endpoints
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
        _post_process_fornecedor,
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
