"""Receipt image storage with local and S3-compatible backends."""
from __future__ import annotations

from dataclasses import dataclass
import mimetypes
import os
from pathlib import Path


class ReceiptImageStoreError(RuntimeError):
    pass


class ReceiptImageStore:
    def put(self, *, business_id: str, filename: str, data: bytes, content_type: str) -> str:
        raise NotImplementedError

    def get(self, *, business_id: str, key: str) -> tuple[bytes, str]:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError


@dataclass
class LocalReceiptImageStore(ReceiptImageStore):
    directory: Path

    def put(self, *, business_id: str, filename: str, data: bytes, content_type: str) -> str:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / filename
        path.write_bytes(data)
        return filename

    def get(self, *, business_id: str, key: str) -> tuple[bytes, str]:
        if Path(key).name != key:
            raise ReceiptImageStoreError("Receipt image key is invalid.")
        path = self.directory / key
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ReceiptImageStoreError("Receipt image is unavailable.") from exc
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return data, content_type

    def delete(self, key: str) -> None:
        (self.directory / key).unlink(missing_ok=True)


class S3ReceiptImageStore(ReceiptImageStore):
    def __init__(self, *, endpoint_url: str, bucket: str, access_key: str, secret_key: str, region: str | None = None):
        import boto3
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def put(self, *, business_id: str, filename: str, data: bytes, content_type: str) -> str:
        key = f"receipts/{business_id}/{filename}"
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        except Exception as exc:
            raise ReceiptImageStoreError("Receipt image object storage is unavailable.") from exc
        return key

    def get(self, *, business_id: str, key: str) -> tuple[bytes, str]:
        expected_prefix = f"receipts/{business_id}/"
        if not key.startswith(expected_prefix):
            raise ReceiptImageStoreError("Receipt image does not belong to this business.")
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            data = response["Body"].read()
        except Exception as exc:
            raise ReceiptImageStoreError("Receipt image object storage is unavailable.") from exc
        content_type = response.get("ContentType") or mimetypes.guess_type(key)[0] or "application/octet-stream"
        return data, content_type

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except Exception:
            pass


def build_receipt_image_store(local_directory: Path) -> ReceiptImageStore:
    endpoint = os.environ.get("SPACES_ENDPOINT_URL", "").strip()
    bucket = os.environ.get("SPACES_BUCKET", "").strip()
    access_key = os.environ.get("SPACES_ACCESS_KEY_ID", "").strip()
    secret_key = os.environ.get("SPACES_SECRET_ACCESS_KEY", "").strip()
    configured = [endpoint, bucket, access_key, secret_key]
    if any(configured) and not all(configured):
        raise RuntimeError("Spaces configuration is incomplete; endpoint, bucket, access key, and secret key are all required.")
    if all(configured):
        return S3ReceiptImageStore(
            endpoint_url=endpoint,
            bucket=bucket,
            access_key=access_key,
            secret_key=secret_key,
            region=os.environ.get("SPACES_REGION") or None,
        )
    return LocalReceiptImageStore(local_directory)
