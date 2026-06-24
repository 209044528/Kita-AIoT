from datetime import timedelta
from io import BytesIO
from uuid import uuid4

from minio import Minio
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Document


def get_minio_client() -> Minio:
    if not settings.MINIO_ENABLED:
        raise RuntimeError("MinIO 未启用，请设置 MINIO_ENABLED=true")
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def ensure_bucket(client: Minio) -> None:
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)


def upload_document(
    db: Session,
    file_name: str,
    content_type: str,
    content: bytes,
    device_id: str | None,
) -> Document:
    client = get_minio_client()
    ensure_bucket(client)
    object_name = f"{device_id or 'shared'}/{uuid4().hex}-{file_name}"
    client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        BytesIO(content),
        length=len(content),
        content_type=content_type,
    )
    document = Document(
        device_id=device_id,
        object_name=object_name,
        file_name=file_name,
        content_type=content_type,
        size=len(content),
        bucket=settings.MINIO_BUCKET,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def presigned_document_url(document: Document) -> str:
    client = get_minio_client()
    return client.presigned_get_object(document.bucket, document.object_name, expires=timedelta(hours=1))
