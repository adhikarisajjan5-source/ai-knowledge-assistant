from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


def create_embeddings(text: str | list[str]) -> object:
    return get_embedding_model().encode(text)
