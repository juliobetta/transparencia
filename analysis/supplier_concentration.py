from typing import Any

import pandas as pd
from sqlalchemy import bindparam, text

from analysis.constants import FORNECEDORES_NATUREZA_MAP


def run(conn: Any, year: int) -> dict:
    sql = text(
        """
        SELECT f.codigo, f.descricao, f.empenhado
        FROM despesas_por_fornecedor f
        LEFT JOIN despesas_gerais g
          ON f.ano = g.ano
          AND f.descricao = g.nomefor
        WHERE f.ano = :ano
        AND g.elemento IN :elementos
        """
    ).bindparams(
        bindparam("elementos", expanding=True, value=list(FORNECEDORES_NATUREZA_MAP.keys())),
    )

    df = pd.read_sql_query(sql, conn, params={"ano": year})
    df["empenhado"] = pd.to_numeric(df["empenhado"].str.replace(",", "."), errors="coerce").fillna(0)
    df = df.groupby(["codigo", "descricao"], as_index=False)["empenhado"].sum()
    total = df["empenhado"].sum()
    df["percentual"] = df["empenhado"] / total * 100 if total > 0 else 0
    top10 = df.nlargest(10, "empenhado").reset_index(drop=True)

    shares = df["empenhado"] / total if total > 0 else df["empenhado"] * 0
    hhi = float((shares**2).sum() * 10000)

    dominant_row = df[df["percentual"] > 40]
    dominante = dominant_row.iloc[0]["descricao"] if not dominant_row.empty else None

    # total_all includes E OUTROS entries excluded from top10 so the pie "Outros" slice is accurate
    df_all = pd.read_sql_query(
        text(
            """
            SELECT f.empenhado
            FROM despesas_por_fornecedor f
            LEFT JOIN despesas_gerais g
              ON f.ano = g.ano
              AND f.descricao = g.nomefor
            WHERE f.ano = :ano
            AND g.elemento IN :elementos
            """
        ).bindparams(
            bindparam("elementos", expanding=True, value=list(FORNECEDORES_NATUREZA_MAP.keys())),
        ),
        conn,
        params={"ano": year},
    )
    df_all["empenhado"] = pd.to_numeric(df_all["empenhado"].str.replace(",", "."), errors="coerce").fillna(0)
    total_all = float(df_all["empenhado"].sum())

    return {"top10": top10, "hhi": hhi, "dominante": dominante, "total_all": total_all}


def concentration_pie(top10: pd.DataFrame, total_all: float) -> pd.DataFrame:
    """Return top10 + 'Outros' slice DataFrame for pie chart rendering."""
    outros = total_all - float(top10["empenhado"].sum())
    slices = top10[["descricao", "empenhado"]].rename(columns={"descricao": "Fornecedor"})
    if outros > 0:
        slices = pd.concat([slices, pd.DataFrame({"Fornecedor": ["Outros"], "empenhado": [outros]})])
    return slices
