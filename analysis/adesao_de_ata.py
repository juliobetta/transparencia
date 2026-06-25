import sqlite3

import pandas as pd


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce").fillna(0)


def run(conn: sqlite3.Connection, year: int, empresa_id: str) -> dict:
    query = """
        SELECT
            l.numero,
            ? as ano,
            l.discr as objeto,
            l.valor as licitacao_valor,
            SUM(c.valcon) as total_c_valor,
            SUM(c.empenhado) as total_c_empenhado,
            l.carona,
            c.mes
        FROM licitacoes l
        LEFT JOIN contratos c
            ON c.licitacao_numero = l.numero
            AND c.ano = l.ano
            AND c.empresa = l.empresa
        WHERE l.ano = ? AND l.empresa = ?
        GROUP BY l.numero, c.mes
    """
    try:
        df = pd.read_sql_query(query, conn, params=(year, year, empresa_id))

        # Add column from join which might be None if no contract matched
        if "total_c_valor" in df.columns:
            df["total_c_valor"] = df["total_c_valor"].fillna(0)

        # Filter for carona here in pandas
        # Need to be very permissive
        df["carona_clean"] = df["carona"].fillna("").astype(str).str.strip().str.upper()

        # Debugging the filter
        df = df[df["carona_clean"] == "S"]

        if df.empty:
            return {
                "list": pd.DataFrame(),
                "count": 0,
                "value": 0.0,
                "total_licitacao": 0.0,
                "contracts_linked_count": 0,
            }

        total_value = float(_to_float(df["total_c_valor"]).sum())
        total_licitacao = float(_to_float(df["licitacao_valor"]).sum())

        # Add a column indicating if a contract is attached (has total_c_valor > 0)
        df["has_contract"] = _to_float(df["total_c_valor"]) > 0

        return {
            "list": df,
            "count": len(df),
            "value": total_value,
            "total_licitacao": total_licitacao,
            "contracts_linked_count": int(df["has_contract"].sum()),
        }
    except Exception as e:
        print(f"DEBUG: Exception in Adesao: {e}")
        return {"list": pd.DataFrame(), "count": 0, "value": 0.0, "total_licitacao": 0.0, "contracts_linked_count": 0}
