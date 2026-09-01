from uuid import UUID

from fastapi import FastAPI, File, HTTPException, UploadFile, status

from app.database import create_database_tables
from app.schemas import AskRequest, SearchRequest
from app.services.document_service import (
    ask_documents,
    delete_document,
    ingest_document,
    list_documents,
    search_documents,
)

app = FastAPI()


@app.on_event("startup")
def initialize_database() -> None:
    create_database_tables()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/documents")
def get_documents() -> list[dict[str, str]]:
    return list_documents()


@app.post("/documents")
async def upload_document(file: UploadFile = File(...)) -> dict[str, str | int]:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are accepted.",
        )

    return ingest_document(file.filename or "", await file.read())


@app.delete("/documents/{document_id}")
def remove_document(document_id: UUID) -> dict[str, str]:
    return delete_document(document_id)


@app.post("/search")
def search_documents_endpoint(
    request: SearchRequest,
) -> dict[str, list[dict[str, str | int | float]]]:
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The search query must not be empty.",
        )

    return search_documents(query)


@app.post("/ask")
def ask_question(
    request: AskRequest,
) -> dict[str, str | list[dict[str, str | int | float]]]:
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The question must not be empty.",
        )

    return ask_documents(question)
