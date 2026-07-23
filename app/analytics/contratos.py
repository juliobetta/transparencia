from typing import Any

import pandas as pd
from sqlalchemy import text


def distribuicao_modalidade(conn: Any, year: int, empresa_ids: list[str] | None = None) -> pd.DataFrame:
    empresa_clause = "AND empresa_id = ANY(:empresas)" if empresa_ids else ""
    params: dict = {"ano": year}
    if empresa_ids:
        params["empresas"] = empresa_ids
    return pd.read_sql_query(
        text(
            f"select modalidade, count(*) as contratos, sum(valor_contrato) as valor"
            f" from fct_contratos where ano = :ano {empresa_clause}"
            f" group by modalidade order by valor desc"
        ),
        conn,
        params=params,
    )


def distribuicao_fundamento_legal(conn: Any, year: int, empresa_ids: list[str] | None = None) -> pd.DataFrame:
    empresa_clause = "AND empresa_id = ANY(:empresas)" if empresa_ids else ""
    params: dict = {"ano": year}
    if empresa_ids:
        params["empresas"] = empresa_ids
    return pd.read_sql_query(
        text(
            f"select fundlegal, count(*) as contratos, sum(valor_contrato) as valor"
            f" from fct_contratos where ano = :ano {empresa_clause}"
            f" group by fundlegal order by valor desc"
        ),
        conn,
        params=params,
    )


def top_fornecedores(conn: Any, year: int, empresa_ids: list[str] | None = None, top_n: int = 10) -> pd.DataFrame:
    empresa_clause = "AND empresa_id = ANY(:empresas)" if empresa_ids else ""
    params: dict = {"ano": year, "top_n": top_n}
    if empresa_ids:
        params["empresas"] = empresa_ids
    return pd.read_sql_query(
        text(
            f"select fornecedor_nome, count(*) as contratos,"
            f" sum(valor_contrato) as valor_total, sum(empenhado) as empenhado_total"
            f" from fct_contratos where ano = :ano {empresa_clause}"
            f" group by fornecedor_nome order by valor_total desc limit :top_n"
        ),
        conn,
        params=params,
    )


def contratos_baixa_execucao(
    conn: Any, year: int, empresa_ids: list[str] | None = None, threshold: float = 0.2
) -> pd.DataFrame:
    empresa_clause = "AND empresa_id = ANY(:empresas)" if empresa_ids else ""
    params: dict = {"ano": year, "threshold": threshold}
    if empresa_ids:
        params["empresas"] = empresa_ids
    return pd.read_sql_query(
        text(
            f"select empresa_id, contrato_numero, fornecedor_nome, objeto,"
            f" valor_contrato, empenhado,"
            f" round(empenhado / nullif(valor_contrato, 0) * 100, 1) as pct_execucao"
            f" from fct_contratos"
            f" where ano = :ano and valor_contrato > 0"
            f" and empenhado / nullif(valor_contrato, 0) < :threshold"
            f" {empresa_clause}"
            f" order by valor_contrato desc"
        ),
        conn,
        params=params,
    )
