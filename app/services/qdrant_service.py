from uuid import uuid4

from fastapi import HTTPException, status
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from app.config import QDRANT_COLLECTION, QDRANT_URL

DOCUMENTS_COLLECTION = QDRANT_COLLECTION
EMBEDDING_DIMENSION = 384


def _qdrant_unavailable(error: Exception) -> None:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Qdrant is unavailable. Start the local Qdrant server at "
            "http://localhost:6333 and try again."
        ),
    ) from error


def _ensure_documents_collection(client: QdrantClient) -> None:
    if not client.collection_exists(DOCUMENTS_COLLECTION):
        client.create_collection(
            collection_name=DOCUMENTS_COLLECTION,
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=models.Distance.COSINE,
            ),
        )


def reject_duplicate_document(document_hash: str) -> None:
    try:
        client = QdrantClient(url=QDRANT_URL)
        _ensure_documents_collection(client)
        existing_points, _ = client.scroll(
            collection_name=DOCUMENTS_COLLECTION,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_hash",
                        match=models.MatchValue(value=document_hash),
                    )
                ]
            ),
            limit=1,
            with_payload=False,
            with_vectors=False,
        )
    except (ResponseHandlingException, UnexpectedResponse) as error:
        _qdrant_unavailable(error)

    if existing_points:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This document has already been uploaded.",
        )


def store_document_chunks(
    filename: str, document_hash: str, chunks: list[str], embeddings: object
) -> None:
    try:
        client = QdrantClient(url=QDRANT_URL)
        _ensure_documents_collection(client)
        points = [
            models.PointStruct(
                id=str(uuid4()),
                vector=[float(value) for value in embedding],
                payload={
                    "filename": filename,
                    "chunk_index": chunk_index,
                    "text": chunk,
                    "document_hash": document_hash,
                },
            )
            for chunk_index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]

        if points:
            client.upsert(collection_name=DOCUMENTS_COLLECTION, points=points)
    except (ResponseHandlingException, UnexpectedResponse) as error:
        _qdrant_unavailable(error)


def search_document_chunks(query_embedding: object) -> list[models.ScoredPoint]:
    try:
        client = QdrantClient(url=QDRANT_URL)
        return client.query_points(
            collection_name=DOCUMENTS_COLLECTION,
            query=[float(value) for value in query_embedding],
            limit=3,
            with_payload=True,
        ).points
    except (ResponseHandlingException, UnexpectedResponse) as error:
        _qdrant_unavailable(error)


def delete_document_chunks(document_hash: str) -> None:
    try:
        client = QdrantClient(url=QDRANT_URL)
        client.delete(
            collection_name=DOCUMENTS_COLLECTION,
            points_selector=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_hash",
                        match=models.MatchValue(value=document_hash),
                    )
                ]
            ),
            wait=True,
        )
    except (ResponseHandlingException, UnexpectedResponse) as error:
        _qdrant_unavailable(error)
