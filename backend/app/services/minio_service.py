import io
from datetime import timedelta
from uuid import UUID

from minio import Minio
from minio.error import S3Error

from app.config import settings

_client: Minio | None = None
_external_client: Minio | None = None


def get_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
    return _client


def get_external_client() -> Minio:
    """Client using the browser-reachable endpoint, for presigned URLs.
    Region is set explicitly to avoid a network call to the unreachable endpoint."""
    global _external_client
    if _external_client is None:
        endpoint = settings.minio_external_endpoint or settings.minio_endpoint
        _external_client = Minio(
            endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
            region="us-east-1",
        )
    return _external_client


def ensure_bucket() -> None:
    client = get_client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def upload_image(user_id: UUID, item_id: UUID, data: bytes, content_type: str, ext: str) -> str:
    """Upload image bytes to MinIO and return the object key."""
    client = get_client()
    key = f"users/{user_id}/clothing/{item_id}.{ext}"
    client.put_object(
        settings.minio_bucket,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return key


def get_presigned_url(key: str) -> str:
    client = get_external_client()
    return client.presigned_get_object(settings.minio_bucket, key, expires=timedelta(hours=1))


def delete_object(key: str) -> None:
    client = get_client()
    try:
        client.remove_object(settings.minio_bucket, key)
    except S3Error:
        pass
