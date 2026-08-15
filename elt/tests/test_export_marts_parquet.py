from pathlib import Path

import duckdb

from elt.export_marts_parquet import export_marts_to_parquet


def test_export_marts_to_parquet(pg, engine, tmp_path: Path, monkeypatch):
    assert engine is not None
    # Simula env vars para o banco do test fixture
    url = pg.url()
    monkeypatch.setenv("DATABASE_URL", url)

    # Executa a exportação para o tmp_path
    exported_files = export_marts_to_parquet(output_dir=tmp_path)

    # Garante que arquivos .parquet foram gerados
    assert len(exported_files) > 0
    for file_path in exported_files:
        assert file_path.exists()
        assert file_path.suffix == ".parquet"

        # Tenta ler o arquivo Parquet gerado via DuckDB para validar integridade
        con = duckdb.connect()
        df = con.execute(f"SELECT * FROM '{file_path}' LIMIT 1").df()
        con.close()
        assert df is not None
