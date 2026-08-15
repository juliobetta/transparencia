"""Exporta tabelas de marts do PostgreSQL para arquivos .parquet comprimidos (Snappy).

Lê a configuração de conexão via DATABASE_URL ou variáveis de ambiente DBT_* / PG*,
conecta ao banco PostgreSQL e exporta todas as tabelas de marts (fct_*, dim_*, seed_*)
do schema public para o diretório target/parquet/.

Uso:
    uv run --project elt python elt/export_marts_parquet.py [--output-dir target/parquet]
"""

import argparse
import os
from pathlib import Path
from urllib.parse import urlparse

import duckdb
from dotenv import load_dotenv

load_dotenv()


def get_db_credentials() -> dict[str, str]:
    """Extrai credenciais de conexão do PostgreSQL a partir das variáveis de ambiente."""
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url:
        u = urlparse(db_url)
        return {
            "host": u.hostname or "localhost",
            "port": str(u.port or 5432),
            "user": u.username or "postgres",
            "password": u.password or "",
            "dbname": u.path.lstrip("/") or "postgres",
        }

    return {
        "host": os.environ.get("DBT_HOST") or os.environ.get("PGHOST") or "localhost",
        "port": os.environ.get("DBT_PORT") or os.environ.get("PGPORT") or "5432",
        "user": os.environ.get("DBT_USER") or os.environ.get("PGUSER") or "postgres",
        "password": os.environ.get("DBT_PASSWORD") or os.environ.get("PGPASSWORD") or "",
        "dbname": os.environ.get("DBT_DBNAME") or os.environ.get("PGDATABASE") or "postgres",
    }


def export_marts_to_parquet(output_dir: Path | str = "target/parquet", schema: str = "public") -> list[Path]:
    """Conecta ao PostgreSQL e exporta as tabelas fct_*, dim_*, seed_* para Parquet."""
    creds = get_db_credentials()
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    duck_conn = duckdb.connect()

    # Tenta usar a extensão postgres nativa do DuckDB; se indisponível, usa fallback SQLAlchemy + pandas
    try:
        duck_conn.execute("INSTALL postgres;")
        duck_conn.execute("LOAD postgres;")

        conn_str = f"host={creds['host']} port={creds['port']} user={creds['user']} dbname={creds['dbname']}"
        if creds["password"]:
            conn_str += f" password={creds['password']}"

        duck_conn.execute(f"ATTACH '{conn_str}' AS pg (TYPE POSTGRES);")

        # Lista tabelas de marts do schema public
        tables_df = duck_conn.execute(
            f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{schema}'
              AND table_type = 'BASE TABLE'
              AND (table_name LIKE 'fct_%' OR table_name LIKE 'dim_%' OR table_name LIKE 'seed_%')
            ORDER BY table_name
            """
        ).fetchall()

        exported_files: list[Path] = []
        for (table_name,) in tables_df:
            target_file = output_path / f"{table_name}.parquet"
            export_sql = f"""
                COPY (SELECT * FROM pg.{schema}.{table_name})
                TO '{target_file}'
                (FORMAT PARQUET, COMPRESSION 'SNAPPY');
            """
            duck_conn.execute(export_sql)
            count_res = duck_conn.execute(f"SELECT COUNT(*) FROM pg.{schema}.{table_name}").fetchone()
            count = count_res[0] if count_res else 0
            print(f"✅ Exportado {table_name} ({count} linhas) -> {target_file}")
            exported_files.append(target_file)

        return exported_files

    except Exception as e:
        print(
            f"⚠️ Alerta: Conexão direta postgres_scanner DuckDB falhou ou indisponível ({e}). Tentando fallback via SQLAlchemy..."
        )
        import pandas as pd
        from sqlalchemy import create_engine, inspect

        user_pwd = f"{creds['user']}:{creds['password']}@" if creds["user"] else ""
        db_uri = f"postgresql://{user_pwd}{creds['host']}:{creds['port']}/{creds['dbname']}"
        engine = create_engine(db_uri)

        inspector = inspect(engine)
        table_names = [t for t in inspector.get_table_names(schema=schema) if t.startswith(("fct_", "dim_", "seed_"))]

        exported_files = []
        for table_name in sorted(table_names):
            target_file = output_path / f"{table_name}.parquet"
            df = pd.read_sql_table(table_name, con=engine, schema=schema)
            duck_conn.register("tmp_df", df)
            duck_conn.execute(f"COPY tmp_df TO '{target_file}' (FORMAT PARQUET, COMPRESSION 'SNAPPY');")
            duck_conn.unregister("tmp_df")
            print(f"✅ [Fallback] Exportado {table_name} ({len(df)} linhas) -> {target_file}")
            exported_files.append(target_file)

        return exported_files
    finally:
        duck_conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta marts PostgreSQL para arquivos Parquet.")
    parser.add_argument(
        "--output-dir",
        default="target/parquet",
        help="Diretório de saída para os arquivos Parquet (padrão: target/parquet)",
    )
    args = parser.parse_args()
    exported = export_marts_to_parquet(output_dir=args.output_dir)
    print(f"\n🎉 Sucesso: {len(exported)} tabelas exportadas para Parquet em {args.output_dir}.")


if __name__ == "__main__":
    main()
