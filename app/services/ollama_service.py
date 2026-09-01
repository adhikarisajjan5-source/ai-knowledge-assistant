import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status
from qdrant_client import models

from app.config import OLLAMA_MODEL, OLLAMA_URL

OLLAMA_GENERATE_URL = f"{OLLAMA_URL.rstrip('/')}/api/generate"


def build_rag_prompt(question: str, results: list[models.ScoredPoint]) -> str:
    context = "\n\n".join(
        (
            f"Source {index + 1} — {payload.get('filename', '')}, "
            f"chunk {payload.get('chunk_index', 0)}:\n{payload.get('text', '')}"
        )
        for index, point in enumerate(results)
        for payload in [point.payload or {}]
    )
    return (
        "Answer only from the provided document context. If the context does not "
        "contain enough information to answer, say that the answer cannot be found "
        "in the documents.\n\n"
        f"Document context:\n{context or '[No matching document chunks were found.]'}\n\n"
        f"Question: {question}\n\nAnswer:"
    )


def generate_answer(prompt: str) -> str:
    request = Request(
        OLLAMA_GENERATE_URL,
        data=json.dumps(
            {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            response_data = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Ollama is unavailable. Start the local Ollama server with the "
                "qwen3:1.7b model and try again."
            ),
        ) from error

    answer = response_data.get("response")
    if not isinstance(answer, str):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama returned an invalid response. Try again after checking Ollama.",
        )

    return answer.strip()
