from typing import Optional

from pydantic import BaseModel


class UpsertTasksDocument(BaseModel):
    content: str
    username: Optional[str] = None

class DocumentTasksSearch(BaseModel):
    text: str
