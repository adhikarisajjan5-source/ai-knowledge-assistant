from tests.test_health import client


def test_search_returns_mocked_results(monkeypatch) -> None:
    expected_results = {
        "results": [
            {
                "filename": "employee-handbook.pdf",
                "chunk_index": 0,
                "text": "Employees may work remotely on Fridays.",
                "similarity_score": 0.91,
            }
        ]
    }

    def fake_search_documents(query: str) -> dict:
        assert query == "remote work"
        return expected_results

    monkeypatch.setattr("app.main.search_documents", fake_search_documents)

    response = client.post("/search", json={"query": "remote work"})

    assert response.status_code == 200
    assert response.json() == expected_results


def test_search_rejects_blank_query() -> None:
    response = client.post("/search", json={"query": "   "})

    assert response.status_code == 400


def test_ask_returns_mocked_answer_and_sources(monkeypatch) -> None:
    expected_response = {
        "answer": "Yes, employees may work remotely on Fridays.",
        "sources": [
            {
                "filename": "employee-handbook.pdf",
                "chunk_index": 0,
                "similarity_score": 0.91,
            }
        ],
    }

    def fake_ask_documents(question: str) -> dict:
        assert question == "Can employees work remotely?"
        return expected_response

    monkeypatch.setattr("app.main.ask_documents", fake_ask_documents)

    response = client.post(
        "/ask", json={"question": "Can employees work remotely?"}
    )

    assert response.status_code == 200
    assert response.json() == expected_response


def test_ask_rejects_blank_question() -> None:
    response = client.post("/ask", json={"question": "   "})

    assert response.status_code == 400
