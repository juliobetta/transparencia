from typing import Any

import pandas as pd
from sqlalchemy import text


def _sum_column(conn: Any, table: str, col: str, year: int, root_only: bool = False) -> float:
    try:
        sql = f"SELECT {col} FROM {table} t WHERE t.ano = :ano"
        if root_only:
            sql += (
                f" AND NOT EXISTS ("
                f"SELECT 1 FROM {table} t2"
                f" WHERE t2.ano = :ano"
                f" AND t2.codigo != t.codigo"
                f" AND t.codigo LIKE RTRIM(t2.codigo, '0.') || '%%'"
                f" AND LENGTH(RTRIM(t2.codigo, '0.')) < LENGTH(RTRIM(t.codigo, '0.'))"
                f")"
            )
        df = pd.read_sql_query(text(sql), conn, params={"ano": year})
        if df.empty:
            return 0.0
        return float(pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce").fillna(0).sum())
    except Exception:
        return 0.0


def run(conn: Any, years: list[int]) -> pd.DataFrame:
    records = []
    for year in years:
        propria_previsto = _sum_column(conn, "receita_orcamentaria", "previsao_atualizada", year, root_only=True)
        propria_arrecadado = _sum_column(conn, "receita_orcamentaria", "arrecadado_total", year, root_only=True)
        if propria_arrecadado == 0:
            propria_arrecadado = _sum_column(conn, "receita_orcamentaria", "arrecadado", year, root_only=True)

        uniao_previsto = _sum_column(conn, "receita_uniao", "previsao_atualizada", year, root_only=True)
        uniao_arrecadado = _sum_column(conn, "receita_uniao", "arrecadado_total", year, root_only=True)
        if uniao_arrecadado == 0:
            uniao_arrecadado = _sum_column(conn, "receita_uniao", "arrecadado", year, root_only=True)

        estado_previsto = _sum_column(conn, "receita_estado", "previsao_atualizada", year, root_only=True)
        estado_arrecadado = _sum_column(conn, "receita_estado", "arrecadado_total", year, root_only=True)
        if estado_arrecadado == 0:
            estado_arrecadado = _sum_column(conn, "receita_estado", "arrecadado", year, root_only=True)

        total_previsto = propria_previsto + uniao_previsto + estado_previsto
        total_arrecadado = propria_arrecadado + uniao_arrecadado + estado_arrecadado

        # Dados de arrecadação real cobrem todo o histórico (import via CSV + API do exercício corrente).
        # Só recorremos à previsão orçamentária quando não há execução alguma ainda (ex.: virada de ano).
        pct_previsto = propria_previsto / total_previsto * 100 if total_previsto > 0 else 0
        pct = propria_arrecadado / total_arrecadado * 100 if total_arrecadado > 0 else pct_previsto

        records.append(
            {
                "ano": year,
                "receita_propria": propria_arrecadado,
                "transferencias_uniao": uniao_arrecadado,
                "transferencias_estado": estado_arrecadado,
                "total": total_arrecadado,
                "pct_propria": pct,
                "pct_propria_previsto": pct_previsto,
                "alerta_dependencia": bool(pct < 10),
                "receita_propria_previsto": propria_previsto,
                "receita_propria_arrecadado": propria_arrecadado,
                "transferencias_uniao_previsto": uniao_previsto,
                "transferencias_uniao_arrecadado": uniao_arrecadado,
                "transferencias_estado_previsto": estado_previsto,
                "transferencias_estado_arrecadado": estado_arrecadado,
                "total_previsto": total_previsto,
                "total_arrecadado": total_arrecadado,
                "pct_arrecadado": total_arrecadado / total_previsto if total_previsto > 0 else 0.0,
            }
        )
    df = pd.DataFrame(records)
    df["alerta_dependencia"] = df["alerta_dependencia"].astype(object)
    df["total_pct_change"] = df["total"].pct_change() * 100
    return df


def tabela_detalhamento(row: "pd.Series") -> "pd.DataFrame":
    """Retorna DataFrame de Previsto vs Arrecadado por fonte de receita, pronto para exibição."""
    data = [
        {
            "Fonte": "Receita Própria (Municipal)",
            "Previsto": row["receita_propria_previsto"],
            "Arrecadado": row["receita_propria_arrecadado"],
        },
        {
            "Fonte": "Transferências da União (Federal)",
            "Previsto": row["transferencias_uniao_previsto"],
            "Arrecadado": row["transferencias_uniao_arrecadado"],
        },
        {
            "Fonte": "Transferências do Estado",
            "Previsto": row["transferencias_estado_previsto"],
            "Arrecadado": row["transferencias_estado_arrecadado"],
        },
    ]
    df = pd.DataFrame(data)
    df["Diferença (Previsto − Arrecadado)"] = df["Previsto"] - df["Arrecadado"]
    df["Realização (%)"] = (df["Arrecadado"] / df["Previsto"]) * 100
    return df
