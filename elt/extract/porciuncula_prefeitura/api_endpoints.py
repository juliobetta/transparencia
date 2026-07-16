from urllib.parse import urlencode

from config import PortalConfig
from elt.extract.base import BaseExtractor, EndpointConfig

_portal = PortalConfig.load()
_base_url = _portal.base_host


def _post_process_contratos(row: dict) -> dict:
    row.setdefault("numero", row.get("codigo", ""))
    proclic = row.get("proclic", "")
    row["licitacao_numero"] = proclic.split("/")[0] if proclic else ""
    row.setdefault("valor", row.get("valcon", ""))
    row.setdefault("data_inicio", row.get("vigeni", ""))
    row.setdefault("data_fim", row.get("vigenf", ""))
    return row


def _post_process_pessoal(row: dict) -> dict:
    if "matricula" not in row or row["matricula"] is None:
        row["matricula"] = row.get("registro")
    return row


def _post_process_despesas_extra_orcamentaria(row: dict) -> dict:
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("numeroguia") or row.get("codigo")
    return row


def _post_process_despesas_gerais(row: dict) -> dict:
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("pkemp") or row.get("codigo")
    return row


def _post_process_despesas_restos_pagar(row: dict) -> dict:
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("codigo")
    return row


def _post_process_diarias(row: dict) -> dict:
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("ordempagamento") or row.get("nempg")
    return row


def _post_process_emendas_cad(row: dict) -> dict:
    if "numero" not in row or row["numero"] is None:
        row["numero"] = row.get("numero_emenda") or row.get("pk_ep_emenda")
    return row


def _post_process_receita_detalhes(row: dict) -> dict:
    if "codigo" not in row or row["codigo"] is None:
        row["codigo"] = row.get("nlanc") or row.get("codre")
    return row


def _post_process_transferencias(row: dict) -> dict:
    if "codigo" not in row or row["codigo"] is None:
        row["codigo"] = row.get("dtlan") or f"{row.get('mes', '')}-{row.get('cnpjrecebedora', '')}"
    return row


def _post_process_despesas_por_exigibilidade(row: dict) -> dict:
    if "tipo" not in row or row["tipo"] is None:
        row["tipo"] = row.get("tipolista")
    if "empenho" not in row or row["empenho"] is None:
        row["empenho"] = row.get("empenho")
    return row


class DespesasExtractor(BaseExtractor):
    def get_params(self, empresa_id: str, year: int) -> dict:
        params = super().get_params(empresa_id, year)
        if self.listagem == "DespesasporExigibilidade":
            params.update(
                {
                    "DiaInicioPeriodo": f"01.01.{year}",
                    "DiaFinalPeriodo": f"31.12.{year}",
                }
            )
            params.pop("MesInicialPeriodo", None)
            params.pop("MesFinalPeriodo", None)
            params.pop("Ano", None)
        return params


class ReceitasExtractor(BaseExtractor):
    def extract(self, empresa_id: str, year: int) -> list[dict]:
        import datetime

        current_year = datetime.date.today().year
        if year != current_year:
            reason = (
                f"O extractor de receitas aceita apenas o ano atual ({current_year}). "
                f"O portal de transparência municipal possui um bug estrutural na API JSON que ignora parâmetros históricos e "
                f"retorna dados incorretos (valores de {current_year} zerados) para anos anteriores. "
                f"Para carregar dados históricos anteriores a {current_year}, utilize o script de importação de CSV correspondente."
            )
            self.logger.warning(reason)
            raise ValueError(reason)
        return super().extract(empresa_id, year)


class LicitacoesExtractor(BaseExtractor):
    pass


class EmendasExtractor(BaseExtractor):
    def get_params(self, empresa_id: str, year: int) -> dict:
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
    def build_url(self, empresa_id: str, year: int) -> str:
        params = {
            "ConectarExercicio": str(year),
            "Listagem": self.listagem,
            "Empresa": str(empresa_id),
            "Ano": str(year),
            "MesFinalPeriodo": "01",
        }
        return f"{self.base_url}{self.base_path}?{urlencode(params)}"


ENDPOINT_CONFIGS: list[EndpointConfig] = [
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasPorOrgao",
        table="despesas_por_orgao",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=DespesasExtractor,
        base_url=_base_url,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasPorUnidade",
        table="despesas_por_unidade",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=DespesasExtractor,
        base_url=_base_url,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasPorFornecedor",
        table="despesas_por_fornecedor",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostrarFornecedor": "True", "MostraDadosConsolidado": "False"},
        extractor_cls=DespesasExtractor,
        base_url=_base_url,
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
        base_url=_base_url,
        post_process=_post_process_despesas_gerais,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasRestosPagar",
        table="despesas_restos_pagar",
        key_cols=["ano", "empresa", "numero"],
        extra={"ApresentaNomeFavorecido": "True", "MostraDadosConsolidado": "False"},
        extractor_cls=DespesasExtractor,
        base_url=_base_url,
        post_process=_post_process_despesas_restos_pagar,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasExtraOrcamentaria",
        table="despesas_extra_orcamentaria",
        key_cols=["ano", "empresa", "numero"],
        extra={"ApresentaNomeFavorecido": "True", "MostraDadosConsolidado": "False"},
        extractor_cls=DespesasExtractor,
        base_url=_base_url,
        post_process=_post_process_despesas_extra_orcamentaria,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasporExigibilidade",
        table="despesas_por_exigibilidade_1",
        key_cols=["ano", "empresa", "tipo", "empenho"],
        extra={"MostraDadosConsolidado": "False", "strTipoLista": "1"},
        extractor_cls=DespesasExtractor,
        base_url=_base_url,
        post_process=_post_process_despesas_por_exigibilidade,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="DespesasporExigibilidade",
        table="despesas_por_exigibilidade_2",
        key_cols=["ano", "empresa", "tipo", "empenho"],
        extra={"MostraDadosConsolidado": "False", "strTipoLista": "2"},
        extractor_cls=DespesasExtractor,
        base_url=_base_url,
        post_process=_post_process_despesas_por_exigibilidade,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Despesas/",
        listagem="Diarias",
        table="diarias",
        key_cols=["ano", "empresa", "numero"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=DespesasExtractor,
        base_url=_base_url,
        post_process=_post_process_diarias,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Receitas/",
        listagem="ReceitaOrcamentaria",
        table="receita_orcamentaria",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=ReceitasExtractor,
        base_url=_base_url,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Receitas/",
        listagem="ReceitaUniao",
        table="receita_uniao",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=ReceitasExtractor,
        base_url=_base_url,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Receitas/",
        listagem="ReceitaEstado",
        table="receita_estado",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=ReceitasExtractor,
        base_url=_base_url,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Receitas/",
        listagem="ReceitaExtraOrcamentaria",
        table="receita_extra_orcamentaria",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=ReceitasExtractor,
        base_url=_base_url,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Receitas/",
        listagem="DetalhesReceitaOrcamentaria",
        table="receita_detalhes",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=ReceitasExtractor,
        base_url=_base_url,
        post_process=_post_process_receita_detalhes,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/LicitacoesEContratos/",
        listagem="Licitacoes",
        table="licitacoes",
        key_cols=["ano", "empresa", "numero"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=LicitacoesExtractor,
        base_url=_base_url,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/LicitacoesEContratos/",
        listagem="Contratos",
        table="contratos",
        key_cols=["ano", "empresa", "numero"],
        extra={"ContratosApenasPublicados": "False", "MostraDadosConsolidado": "False"},
        extractor_cls=LicitacoesExtractor,
        base_url=_base_url,
        post_process=_post_process_contratos,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Transferencias/",
        listagem="Transf",
        table="transferencias",
        key_cols=["ano", "empresa", "codigo"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=TransferenciasExtractor,
        base_url=_base_url,
        post_process=_post_process_transferencias,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Transferencias/",
        listagem="EmendasImpositivasArt166A",
        table="emendas_impositivas",
        key_cols=["ano", "empresa", "numero"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=EmendasExtractor,
        base_url=_base_url,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Transferencias/",
        listagem="CadEmendasImpositivas",
        table="emendas_cad",
        key_cols=["ano", "empresa", "numero"],
        extra={"MostraDadosConsolidado": "False"},
        extractor_cls=EmendasExtractor,
        base_url=_base_url,
        post_process=_post_process_emendas_cad,
    ),
    EndpointConfig(
        base_path="/Transparencia/VersaoJson/Pessoal/",
        listagem="Servidores",
        table="pessoal",
        key_cols=["ano", "empresa", "mes", "matricula"],
        extra={},
        extractor_cls=PessoalExtractor,
        base_url=_base_url,
        post_process=_post_process_pessoal,
    ),
]
