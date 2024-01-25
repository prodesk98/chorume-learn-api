from typing import Optional
from pydantic import BaseModel


class UpsertTasksDocument(BaseModel):
    content: str
    username: Optional[str] = None
    namespace: Optional[str] = "default"

class DocumentTasksSearch(BaseModel):
    id: str
    text: str
    namespace: str
