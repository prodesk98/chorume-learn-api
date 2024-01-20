from typing import List, Optional
from pydantic import BaseModel, AnyUrl


class ShowMillionResponse(BaseModel):
    question: Optional[str] = None
    alternatives: Optional[List[str]] = []
    truth: Optional[int] = -1
    voice_url: Optional[AnyUrl] = None
