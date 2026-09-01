from app.services.document_service import chunk_text


def test_chunk_text_returns_one_chunk_for_short_text() -> None:
    text = "Short text"

    chunks = chunk_text(text)

    assert chunks == [text]


def test_chunk_text_splits_long_text() -> None:
    text = "".join(f"{index:04d}" for index in range(300))

    chunks = chunk_text(text)

    assert len(chunks) > 1


def test_chunk_text_keeps_the_configured_overlap() -> None:
    text = "".join(f"{index:04d}" for index in range(300))

    chunks = chunk_text(text)

    assert chunks[0][-200:] == chunks[1][:200]


def test_chunk_text_returns_no_chunks_for_empty_text() -> None:
    assert chunk_text("") == []
