import hashlib
from io import BytesIO
from uuid import UUID

from fastapi import HTTPException, status
from pypdf import PdfReader
from qdrant_client import models
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.database import SessionLocal
from app.models import Document
from app.services.embedding_service import create_embeddings
from app.services.ollama_service import build_rag_prompt, generate_answer
from app.services.qdrant_service import (
    delete_document_chunks,
    reject_duplicate_document,
    search_document_chunks,
    store_document_chunks,
)


def chunk_text(
    text: str, chunk_size: int = 1000, chunk_overlap: int = 200
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError("chunk_overlap must be at least zero and smaller than chunk_size.")

    chunks: list[str] = []
    start = 0
    step = chunk_size - chunk_overlap

    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += step

    return chunks


def _postgres_unavailable(error: SQLAlchemyError) -> None:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="PostgreSQL is unavailable. Check the local database and try again.",
    ) from error


def _save_document_metadata(filename: str, document_hash: str) -> None:
    session = SessionLocal()
    try:
        session.add(Document(filename=filename, document_hash=document_hash))
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This document has already been uploaded.",
        ) from error
    except SQLAlchemyError as error:
        session.rollback()
        _postgres_unavailable(error)
    finally:
        session.close()


def ingest_document(filename: str, pdf_content: bytes) -> dict[str, str | int]:
    document_hash = hashlib.sha256(pdf_content).hexdigest()
    reject_duplicate_document(document_hash)

    reader = PdfReader(BytesIO(pdf_content))
    extracted_text = "".join(page.extract_text() or "" for page in reader.pages)
    chunks = chunk_text(extracted_text)
    embeddings = create_embeddings(chunks) if chunks else []
    embedding_dimension = len(embeddings[0]) if len(embeddings) > 0 else 0

    store_document_chunks(filename, document_hash, chunks, embeddings)
    _save_document_metadata(filename, document_hash)

    response: dict[str, str | int] = {
        "filename": filename,
        "page_count": len(reader.pages),
        "total_characters": len(extracted_text),
        "chunk_count": len(chunks),
        "embedding_count": len(embeddings),
        "embedding_dimension": embedding_dimension,
        "first_chunk": chunks[0] if chunks else "",
    }

    if not extracted_text.strip():
        response["message"] = (
            "No extractable text was found. This PDF may contain scanned images."
        )

    return response


def _retrieve_document_chunks(query: str) -> list[models.ScoredPoint]:
    return search_document_chunks(create_embeddings(query))


def search_documents(query: str) -> dict[str, list[dict[str, str | int | float]]]:
    results = _retrieve_document_chunks(query)
    return {
        "results": [
            {
                "filename": str((point.payload or {}).get("filename", "")),
                "chunk_index": int((point.payload or {}).get("chunk_index", 0)),
                "text": str((point.payload or {}).get("text", "")),
                "similarity_score": float(point.score),
            }
            for point in results
        ]
    }


def ask_documents(question: str) -> dict[str, str | list[dict[str, str | int | float]]]:
    results = _retrieve_document_chunks(question)
    answer = generate_answer(build_rag_prompt(question, results))
    return {
        "answer": answer,
        "sources": [
            {
                "filename": str((point.payload or {}).get("filename", "")),
                "chunk_index": int((point.payload or {}).get("chunk_index", 0)),
                "similarity_score": float(point.score),
            }
            for point in results
        ],
    }


def list_documents() -> list[dict[str, str]]:
    session = SessionLocal()
    try:
        documents = session.scalars(
            select(Document).order_by(Document.created_at.desc())
        ).all()
        return [
            {
                "id": str(document.id),
                "filename": document.filename,
                "created_at": document.created_at.isoformat(),
            }
            for document in documents
        ]
    except SQLAlchemyError as error:
        _postgres_unavailable(error)
    finally:
        session.close()


def delete_document(document_id: UUID) -> dict[str, str]:
    session = SessionLocal()
    try:
        document = session.get(Document, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        delete_document_chunks(document.document_hash)
        session.delete(document)
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        _postgres_unavailable(error)
    finally:
        session.close()

    return {"message": "Document deleted successfully."}
