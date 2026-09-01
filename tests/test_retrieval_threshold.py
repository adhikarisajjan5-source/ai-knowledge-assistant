from types import SimpleNamespace

from app.services import document_service, qdrant_service
from tests.test_health import client


def test_search_filters_out_low_score_results(monkeypatch) -> None:
    high_score_point = SimpleNamespace(score=0.8)
    low_score_point = SimpleNamespace(score=0.2)

    class FakeQdrantClient:
        def __init__(self, url: str) -> None:
            assert url == qdrant_service.QDRANT_URL

        def query_points(self, **kwargs):
            assert kwargs["limit"] == 3
            assert kwargs["score_threshold"] == qdrant_service.QDRANT_SCORE_THRESHOLD
            return SimpleNamespace(points=[high_score_point, low_score_point])

    monkeypatch.setattr(qdrant_service, "QdrantClient", FakeQdrantClient)

    results = qdrant_service.search_document_chunks([0.1] * 384)

    assert results == [high_score_point]


def test_ask_returns_fallback_without_calling_ollama(monkeypatch) -> None:
    def fake_generate_answer(prompt: str) -> str:
        raise AssertionError("Ollama should not be called without relevant chunks.")

    monkeypatch.setattr(document_service, "_retrieve_document_chunks", lambda _: [])
    monkeypatch.setattr(document_service, "generate_answer", fake_generate_answer)

    response = client.post(
        "/ask", json={"question": "Can employees work remotely?"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "The answer cannot be found in the documents.",
        "sources": [],
    }
