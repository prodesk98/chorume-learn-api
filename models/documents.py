from typing import Optional, List

from pydantic import BaseModel


class Metadata(BaseModel):
    text: str


class Document(BaseModel):
    id: Optional[str] = None
    vector: List[float] = []
    metadata: Optional[Metadata] = None
