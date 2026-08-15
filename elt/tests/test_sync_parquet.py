from pathlib import Path
from unittest.mock import MagicMock

from elt.scripts.sync_parquet import ensure_bucket_exists, sync_local_dir_to_s3


def test_ensure_bucket_exists_creates_when_missing():
    mock_s3 = MagicMock()
    from botocore.exceptions import ClientError

    mock_s3.head_bucket.side_effect = ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket")

    ensure_bucket_exists(mock_s3, "test-bucket")

    mock_s3.head_bucket.assert_called_once_with(Bucket="test-bucket")
    mock_s3.create_bucket.assert_called_once_with(Bucket="test-bucket")


def test_sync_local_dir_to_s3_uploads_parquet_files(tmp_path: Path):
    # Criar arquivo .parquet simulado
    parquet_dir = tmp_path / "parquet"
    parquet_dir.mkdir()
    sample_file = parquet_dir / "fct_posicao_fiscal_metricas.parquet"
    sample_file.write_bytes(b"PAR1_sample_bytes")

    mock_s3 = MagicMock()
    from botocore.exceptions import ClientError

    mock_s3.head_object.side_effect = ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject")

    sync_local_dir_to_s3(mock_s3, "transparencia-marts", parquet_dir)

    mock_s3.upload_file.assert_called_once_with(
        Filename=str(sample_file),
        Bucket="transparencia-marts",
        Key="fct_posicao_fiscal_metricas.parquet",
        ExtraArgs={"ContentType": "application/vnd.apache.parquet"},
    )
