from elt.extract.base import BaseExtractor


class PorciunculaExtractor(BaseExtractor):
    def get_params(self, empresa_id: str, year: int) -> dict:
        return {
            "ConectarExercicio": str(year),
            "Listagem": self.listagem,
            "DiaInicioPeriodo": "01",
            "MesInicialPeriodo": "01",
            "DiaFinalPeriodo": "31",
            "MesFinalPeriodo": "12",
            "Ano": str(year),
            "Empresa": str(empresa_id),
            "MostraDadosConsolidado": "False",
            **self.extra,
        }
