from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str


class AskRequest(BaseModel):
    question: str
