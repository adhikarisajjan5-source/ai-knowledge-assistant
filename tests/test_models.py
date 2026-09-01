from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Document

TEST_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_knowledge_test"


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
        engine.dispose()


def test_document_can_be_inserted_and_queried(db_session: Session) -> None:
    document_hash = uuid4().hex
    document = Document(filename="employee-handbook.pdf", document_hash=document_hash)
    db_session.add(document)
    db_session.flush()

    saved_document = db_session.scalar(
        select(Document).where(Document.document_hash == document_hash)
    )

    assert saved_document is not None
    assert saved_document.filename == "employee-handbook.pdf"
    assert saved_document.document_hash == document_hash


def test_document_hash_must_be_unique(db_session: Session) -> None:
    document_hash = uuid4().hex
    db_session.add(Document(filename="first.pdf", document_hash=document_hash))
    db_session.flush()

    db_session.add(Document(filename="duplicate.pdf", document_hash=document_hash))

    with pytest.raises(IntegrityError):
        db_session.flush()
