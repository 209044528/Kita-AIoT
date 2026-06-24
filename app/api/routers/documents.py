from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.serializers import model_to_dict
from app.models import Device, Document
from app.services.storage import presigned_document_url, upload_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", status_code=201)
async def create_document(
    file: UploadFile = File(...),
    device_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Agent tool 5: upload a device document or image to MinIO."""
    if device_id and not db.get(Device, device_id):
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    try:
        document = upload_document(
            db,
            file.filename or "document.bin",
            file.content_type or "application/octet-stream",
            content,
            device_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return model_to_dict(document)


@router.get("/")
def list_documents(
    device_id: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    statement = select(Document).order_by(Document.created_at.desc())
    if device_id:
        statement = statement.where(Document.device_id == device_id)
    documents = list(db.scalars(statement.limit(100)))
    return {"count": len(documents), "documents": [model_to_dict(item) for item in documents]}


@router.get("/{document_id}/download-url")
def get_document_download_url(
    document_id: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        url = presigned_document_url(document)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"document_id": document_id, "url": url, "expires_in": "1h"}
