from urllib.parse import urlencode

from .base import BASE_URL, BaseExtractor, EndpointConfig


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


def _post_process_despesas_por_exigibilidade(row: dict) -> dict:
    # API sends TIPOLISTA; model uses "tipo".
    if "tipo" not in row or row["tipo"] is None:
        row["tipo"] = row.get("tipolista")
    # API sends EMPENHO; model needs it for PK.
    if "empenho" not in row or row["empenho"] is None:
        row["empenho"] = row.get("empenho")
    return row


class DespesasExtractor(BaseExtractor):
    def get_params(self, empresa_id: int, year: int) -> dict:
        params = super().get_params(empresa_id, year)
        if self.listagem == "DespesasporExigibilidade":
            # Override date range for this specific endpoint
            params.update(
                {
                    "DiaInicioPeriodo": f"01.01.{year}",
                    "DiaFinalPeriodo": f"31.12.{year}",
                    # "strTipoLista" is already in self.extra
                }
            )
            # Remove keys that are not needed for this endpoint
            params.pop("MesInicialPeriodo", None)
            params.pop("MesFinalPeriodo", None)
            params.pop("Ano", None)
        return params


class ReceitasExtractor(BaseExtractor):
    pass


class LicitacoesExtractor(BaseExtractor):
    pass


class EmendasExtractor(BaseExtractor):
    def get_params(self, empresa_id: int, year: int) -> dict:
        if self.listagem in ["EmendasImpositivasArt166A", "CadEmendasImpositivas"]:
            return {
                "ConectarExercicio": str(year),
                "Listagem": self.listagem,
                "Empresa": str(empresa_id),
                "MostraDadosConsolidado": "False",
                **self.extra,
            }

        return super().get_params(empresa_id, year)


class TransferenciasExtractor(BaseExtractor):
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
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasPorOrgao",
        table="despesas_por_orgao",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=DespesasExtractor,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasPorUnidade",
        table="despesas_por_unidade",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=DespesasExtractor,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasPorFornecedor",
        table="despesas_por_fornecedor",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostrarFornecedor": "True", "MostraDadosConsolidado": "False"},
        extractor_cls=DespesasExtractor,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasGerais",
        table="despesas_gerais",
        key_cols=["ano", "empresa", "numero"],
        extra={
            "MostrarFornecedor": "True",
            "MostrarCNPJFornecedor": "True",
            "UFParaFiltroCOVID": "",
            "ApenasIDEmpenho": "False",
        },
        extractor_cls=DespesasExtractor,
        post_process=_post_process_despesas_gerais,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasRestosPagar",
        table="despesas_restos_pagar",
        key_cols=["ano", "empresa", "numero"],
        extra={"ApresentaNomeFavorecido": "True", "MostraDadosConsolidado": "False"},
        extractor_cls=DespesasExtractor,
        post_process=_post_process_despesas_restos_pagar,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasExtraOrcamentaria",
        table="despesas_extra_orcamentaria",
        key_cols=["ano", "empresa", "numero"],
        extra={"ApresentaNomeFavorecido": "True", "MostraDadosConsolidado": "False"},
        extractor_cls=DespesasExtractor,
        post_process=_post_process_despesas_extra_orcamentaria,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasporExigibilidade",
        table="despesas_por_exigibilidade_1",
        key_cols=["ano", "empresa", "tipo", "empenho"],
        extra={"MostraDadosConsolidado": "False", "strTipoLista": "1"},
        extractor_cls=DespesasExtractor,
        post_process=_post_process_despesas_por_exigibilidade,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasporExigibilidade",
        table="despesas_por_exigibilidade_2",
        key_cols=["ano", "empresa", "tipo", "empenho"],
        extra={"MostraDadosConsolidado": "False", "strTipoLista": "2"},
        extractor_cls=DespesasExtractor,
        post_process=_post_process_despesas_por_exigibilidade,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="Diarias",
        table="diarias",
        key_cols=["ano", "empresa", "numero"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=DespesasExtractor,
        post_process=_post_process_diarias,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Receitas/",
        listagem="ReceitaOrcamentaria",
        table="receita_orcamentaria",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=ReceitasExtractor,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Receitas/",
        listagem="ReceitaUniao",
        table="receita_uniao",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=ReceitasExtractor,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Receitas/",
        listagem="ReceitaEstado",
        table="receita_estado",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=ReceitasExtractor,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Receitas/",
        listagem="ReceitaExtraOrcamentaria",
        table="receita_extra_orcamentaria",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=ReceitasExtractor,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Receitas/",
        listagem="DetalhesReceitaOrcamentaria",
        table="receita_detalhes",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=ReceitasExtractor,
        post_process=_post_process_receita_detalhes,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/LicitacoesEContratos/",
        listagem="Licitacoes",
        table="licitacoes",
        key_cols=["ano", "empresa", "numero"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=LicitacoesExtractor,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/LicitacoesEContratos/",
        listagem="Contratos",
        table="contratos",
        key_cols=["ano", "empresa", "numero"],
        extra={"ContratosApenasPublicados": "False", "MostraDadosConsolidado": "False"},
        extractor_cls=LicitacoesExtractor,
        post_process=_post_process_contratos,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Transferencias/",
        listagem="Transf",
        table="transferencias",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=TransferenciasExtractor,
        post_process=_post_process_transferencias,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Transferencias/",
        listagem="EmendasImpositivasArt166A",
        table="emendas_impositivas",
        key_cols=["ano", "empresa", "numero"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=EmendasExtractor,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Transferencias/",
        listagem="CadEmendasImpositivas",
        table="emendas_cad",
        key_cols=["ano", "empresa", "numero"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=EmendasExtractor,
        post_process=_post_process_emendas_cad,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Pessoal/",
        listagem="Servidores",
        table="pessoal",
        key_cols=["ano", "empresa", "mes", "matricula"],
        extra={},
        extractor_cls=PessoalExtractor,
        post_process=_post_process_pessoal,
    ),
]
