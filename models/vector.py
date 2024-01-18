from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from pydantic import BaseModel


class Vector(BaseModel):
    uuid: Optional[str] = None
    id: Optional[str] = None
    content: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, id: str, content: str, created_by: str):
        return cls(
            uuid=str(uuid4()),
            id=id,
            content=content,
            created_by=created_by,
            created_at=datetime.now(),
        )

class SelectVectorFactoryRequest(BaseModel):
    filter: dict

class AllVectorFactoryRequest(BaseModel):
    filter: dict = {}
    sort: dict = {}
    skip: Optional[int] = 0
    limit: Optional[int] = 100

class AllDeleteVectorFactoryRequest(BaseModel):
    ids: List[str]
