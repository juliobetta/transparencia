from typing import Any

import pandas as pd
from sqlalchemy import bindparam, text

from analysis.constants import FORNECEDORES_NATUREZA_MAP


def run(conn: Any, year: int, empresa_id: str | None = None) -> dict:
    empresa_clause = "AND f.empresa = :empresa" if empresa_id else ""
    params: dict = {"ano": year}
    if empresa_id:
        params["empresa"] = empresa_id

    sql = text(
        f"""
        SELECT f.codigo, f.descricao, f.empenhado
        FROM despesas_por_fornecedor f
        LEFT JOIN despesas_gerais g
          ON f.ano = g.ano
          AND f.descricao = g.nomefor
        WHERE f.ano = :ano
        {empresa_clause}
        AND g.elemento IN :elementos
        """
    ).bindparams(
        bindparam("elementos", expanding=True, value=list(FORNECEDORES_NATUREZA_MAP.keys())),
    )

    df = pd.read_sql_query(sql, conn, params=params)
    df["empenhado"] = pd.to_numeric(df["empenhado"].str.replace(",", "."), errors="coerce").fillna(0)
    df = df.groupby(["codigo", "descricao"], as_index=False)["empenhado"].sum()
    total = df["empenhado"].sum()
    df["percentual"] = df["empenhado"] / total * 100 if total > 0 else 0
    top10 = df.nlargest(10, "empenhado").reset_index(drop=True)

    shares = df["empenhado"] / total if total > 0 else df["empenhado"] * 0
    hhi = float((shares**2).sum() * 10000)

    linha_dominante = df[df["percentual"] > 40]
    dominante = linha_dominante.iloc[0]["descricao"] if not linha_dominante.empty else None

    # total_all inclui entradas "E OUTROS" excluídas do top10 para que a fatia "Outros" do piechart seja precisa
    df_all = pd.read_sql_query(
        text(
            f"""
            SELECT f.empenhado
            FROM despesas_por_fornecedor f
            LEFT JOIN despesas_gerais g
              ON f.ano = g.ano
              AND f.descricao = g.nomefor
            WHERE f.ano = :ano
            {empresa_clause}
            AND g.elemento IN :elementos
            """
        ).bindparams(
            bindparam("elementos", expanding=True, value=list(FORNECEDORES_NATUREZA_MAP.keys())),
        ),
        conn,
        params=params,
    )
    df_all["empenhado"] = pd.to_numeric(df_all["empenhado"].str.replace(",", "."), errors="coerce").fillna(0)
    total_all = float(df_all["empenhado"].sum())

    return {"top10": top10, "hhi": hhi, "dominante": dominante, "total_all": total_all}


def piechart_concentracao(top10: pd.DataFrame, total_all: float) -> pd.DataFrame:
    outros = total_all - float(top10["empenhado"].sum())
    slices = top10[["descricao", "empenhado"]].rename(columns={"descricao": "Fornecedor"})
    if outros > 0:
        slices = pd.concat([slices, pd.DataFrame({"Fornecedor": ["Outros"], "empenhado": [outros]})])
    return slices


def hhi_por_ano(conn: Any, years: list[int], empresa_id: str | None = None) -> dict[int, float]:
    return {year: run(conn, year, empresa_id=empresa_id)["hhi"] for year in years}
