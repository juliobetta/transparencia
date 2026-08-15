"""Script de sincronização de arquivos .parquet para Cloudflare R2 / MinIO S3 local."""

import hashlib
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, "../../.env")

if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()


def get_file_md5(file_path: Path) -> str:
    """Calcula o hash MD5 em hex do arquivo local."""
    hasher = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_dest_s3_client_and_bucket() -> tuple[Any, str, bool]:
    """Retorna o cliente S3 de destino, o nome da bucket e se é o Cloudflare R2 (True) ou MinIO local (False)."""
    r2_account_id = os.getenv("R2_ACCOUNT_ID")
    r2_access_key = os.getenv("R2_ACCESS_KEY_ID")
    r2_secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
    r2_bucket_name = os.getenv("R2_BUCKET_NAME", "transparencia-parquet-store")

    if r2_account_id and r2_access_key and r2_secret_key:
        endpoint_url = f"https://{r2_account_id}.r2.cloudflarestorage.com"
        print(f"[sync_parquet] Conectando ao destino Cloudflare R2 ({endpoint_url})...")
        s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
            region_name="auto",
        )
        return s3_client, r2_bucket_name, True

    # Fallback local para MinIO S3
    endpoint_url = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
    bucket_name = os.getenv("S3_BUCKET_NAME", "transparencia-marts")

    print(f"[sync_parquet] Fallback local: Conectando ao MinIO S3 ({endpoint_url})...")
    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",
    )
    return s3_client, bucket_name, False


def get_local_source_s3_client() -> tuple[Any, str]:
    """Retorna o cliente S3 local do MinIO para leitura dos objetos Parquet gerados pelo dbt."""
    endpoint_url = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
    bucket_name = os.getenv("S3_BUCKET_NAME", "transparencia-marts")

    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",
    )
    return s3_client, bucket_name


def ensure_bucket_exists(s3_client: Any, bucket_name: str) -> None:
    """Garante que a bucket existe no destino antes do upload."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        print(f"[sync_parquet] Bucket '{bucket_name}' não encontrada no destino. Criando...")
        try:
            s3_client.create_bucket(Bucket=bucket_name)
        except Exception as e:
            print(f"[sync_parquet] Alerta ao criar bucket '{bucket_name}': {e}")


def sync_from_local_s3_to_r2(dest_s3: Any, dest_bucket: str) -> None:
    """Copia os objetos .parquet do MinIO S3 local diretamente para o Cloudflare R2."""
    source_s3, source_bucket = get_local_source_s3_client()
    try:
        resp = source_s3.list_objects_v2(Bucket=source_bucket)
    except Exception as err:
        print(f"[sync_parquet] Erro ao listar objetos no MinIO S3 local: {err}")
        return

    contents = resp.get("Contents", [])
    parquet_objects = [
        obj for obj in contents if obj["Key"].endswith(".parquet") and not obj["Key"].startswith((".", "{"))
    ]

    if not parquet_objects:
        print(f"[sync_parquet] Nenhum objeto .parquet encontrado na bucket local '{source_bucket}'.")
        return

    print(
        f"[sync_parquet] Encontrados {len(parquet_objects)} objetos .parquet no MinIO S3 para sincronização com o R2."
    )
    ensure_bucket_exists(dest_s3, dest_bucket)

    uploaded_count = 0
    skipped_count = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        for obj in parquet_objects:
            key = obj["Key"]
            size = obj["Size"]

            should_upload = True
            try:
                head_resp = dest_s3.head_object(Bucket=dest_bucket, Key=key)
                if head_resp.get("ContentLength", -1) == size:
                    should_upload = False
                    skipped_count += 1
            except ClientError:
                should_upload = True

            if should_upload:
                print(f"  -> Sincronizando para R2: {key} ({size} bytes)")
                local_file = tmp_path / Path(key).name
                source_s3.download_file(source_bucket, key, str(local_file))

                dest_s3.upload_file(
                    Filename=str(local_file),
                    Bucket=dest_bucket,
                    Key=key,
                    ExtraArgs={"ContentType": "application/vnd.apache.parquet"},
                )
                uploaded_count += 1
                local_file.unlink(missing_ok=True)
            else:
                print(f"  -> Ignorado no R2 (em dia): {key}")

    print(
        f"[sync_parquet] Sincronização com Cloudflare R2 concluída com sucesso! ({uploaded_count} enviados, {skipped_count} mantidos)"
    )


def sync_local_dir_to_s3(dest_s3: Any, dest_bucket: str, target_dir: Path) -> None:
    """Sincroniza arquivos .parquet de um diretório de arquivos local para o destino S3/R2."""
    ensure_bucket_exists(dest_s3, dest_bucket)
    parquet_files = [f for f in target_dir.rglob("*.parquet") if f.is_file() and not f.name.startswith((".", "{"))]

    if not parquet_files:
        print(f"[sync_parquet] Nenhum arquivo .parquet válido encontrado no diretório local '{target_dir}'.")
        return

    print(f"[sync_parquet] Encontrados {len(parquet_files)} arquivos .parquet em '{target_dir}'.")
    uploaded_count = 0
    skipped_count = 0

    for file_path in parquet_files:
        relative_key = file_path.relative_to(target_dir).as_posix()
        file_size = file_path.stat().st_size

        should_upload = True
        try:
            head_resp = dest_s3.head_object(Bucket=dest_bucket, Key=relative_key)
            if head_resp.get("ContentLength", -1) == file_size:
                should_upload = False
                skipped_count += 1
        except ClientError:
            should_upload = True

        if should_upload:
            print(f"  -> Uploading: {relative_key} ({file_size} bytes)")
            dest_s3.upload_file(
                Filename=str(file_path),
                Bucket=dest_bucket,
                Key=relative_key,
                ExtraArgs={"ContentType": "application/vnd.apache.parquet"},
            )
            uploaded_count += 1
        else:
            print(f"  -> Ignorado (em dia): {relative_key}")

    print(f"[sync_parquet] Sincronização concluída com sucesso! ({uploaded_count} enviados, {skipped_count} mantidos)")


def main() -> None:
    """Ponto de entrada principal do script."""
    elt_dir = Path(__file__).resolve().parent.parent
    repo_root = elt_dir.parent
    dest_s3, dest_bucket, is_r2 = get_dest_s3_client_and_bucket()

    # 1. Se estiver enviando para o Cloudflare R2 (produção/staging)
    if is_r2:
        sync_from_local_s3_to_r2(dest_s3, dest_bucket)
        return

    # 2. Procurar arquivos em diretórios locais do sistema de arquivos
    candidate_dirs = [
        repo_root / "target" / "parquet",
        elt_dir / "transform" / "target" / "parquet",
        elt_dir / "transform" / "target",
        elt_dir / "target",
    ]
    target_dir = next(
        (
            d
            for d in candidate_dirs
            if d.exists() and any(f.is_file() and not f.name.startswith((".", "{")) for f in d.rglob("*.parquet"))
        ),
        None,
    )

    if target_dir:
        sync_local_dir_to_s3(dest_s3, dest_bucket, target_dir)
        return

    # 3. Se não houver diretório local com Parquets, tenta ler do MinIO S3 local
    try:
        source_s3, source_bucket = get_local_source_s3_client()
        resp = source_s3.list_objects_v2(Bucket=source_bucket)
        objs = [
            o for o in resp.get("Contents", []) if o["Key"].endswith(".parquet") and not o["Key"].startswith((".", "{"))
        ]
        if objs:
            print(f"[sync_parquet] Fallback local OK: {len(objs)} arquivos .parquet presentes no MinIO S3 local.")
            return
    except Exception:
        pass

    print("[sync_parquet] Nenhum arquivo Parquet localizado para sincronização.")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"[sync_parquet] Erro fatal durante a sincronização: {err}", file=sys.stderr)
        sys.exit(1)
