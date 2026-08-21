import re
from pathlib import Path

from sqlalchemy import text


def test_marts_index_post_hooks_syntax_and_columns(engine):
    """Valida se todas as DDLs de CREATE INDEX nos post_hooks dos marts dbt

    são sintaticamente válidas no PostgreSQL, usam a função immutable_unaccent

    e referenciam colunas que realmente existem no modelo dbt.

    """

    marts_dir = Path(__file__).parent.parent.parent / "transform" / "models" / "marts"

    sql_files = list(marts_dir.glob("*.sql"))

    assert len(sql_files) > 0, "Nenhum modelo mart encontrado"

    with engine.connect() as conn:
        # Garante que a extensão unaccent e a função auxiliar imutável existam

        conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))

        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

        conn.execute(
            text(
                "CREATE OR REPLACE FUNCTION immutable_unaccent(text) RETURNS text AS $$ "
                "SELECT public.unaccent($1) $$ LANGUAGE sql IMMUTABLE PARALLEL SAFE"
            )
        )

        conn.commit()

        for file_path in sql_files:
            content = file_path.read_text()

            # Extrai todas as queries CREATE INDEX dos post_hooks (mesmo se desativadas por test_mode)

            indexes = re.findall(r"CREATE INDEX IF NOT EXISTS [^\"]+", content)

            if not indexes:
                continue

            table_name = file_path.stem

            # Obter colunas existentes na view/tabela mart criada pelo dbt

            res = conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = :tname"
                ),
                {"tname": table_name},
            )

            existing_columns = {row[0] for row in res.fetchall()}

            assert existing_columns, f"Tabela/view {table_name} não foi encontrada no schema public"

            # Cria tabela temporária real com a mesma estrutura para testar DDL do índice

            tmp_table = f"tmp_idx_test_{table_name}"

            conn.execute(text(f'CREATE TEMP TABLE "{tmp_table}" AS SELECT * FROM public."{table_name}" WITH NO DATA'))

            conn.commit()

            for idx_ddl in indexes:
                # Limpa tags Jinja como {% endif %} para obter a query SQL pura

                clean_ddl = re.sub(r"\s*{%\s*endif\s*%}.*", "", idx_ddl).strip()

                # 1. Garante que não use unaccent(...) diretamente em índice de expressão sem wrapper imutável

                raw_without_immutable = clean_ddl.replace("immutable_unaccent", "")

                assert "unaccent(" not in raw_without_immutable, (
                    f"Índice em {file_path.name} usa 'unaccent' que é STABLE. "
                    f"Deve usar 'immutable_unaccent': {clean_ddl}"
                )

                # 2. Testa execução real da DDL do índice na tabela temporária no Postgres

                idx_query = clean_ddl.replace("{{ this }}", f'"{tmp_table}"')

                try:
                    conn.execute(text(idx_query))

                    conn.commit()

                except Exception as e:
                    assert False, f"Falha ao executar DDL de índice em {file_path.name}: {idx_query}\nErro: {e}"

            conn.execute(text(f'DROP TABLE IF EXISTS "{tmp_table}"'))

            conn.commit()
