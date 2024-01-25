from typing import Optional, List
from pydantic import BaseModel, Field, AnyUrl


class UpsertResponse(BaseModel):
    success: Optional[bool] = True

class UpsertRequest(BaseModel):
    content: Optional[str] = Field(..., max_length=4000)
    username: Optional[str] = None
    namespace: Optional[str] = None

class QueryResponse(BaseModel):
    success: Optional[bool] = True
    responses: Optional[List[dict]] = []

class AnswerResponse(BaseModel):
    success: Optional[bool] = True
    response: Optional[str] = None

class TextToVoiceRequest(BaseModel):
    content: Optional[str] = None

class TextToVoiceResponse(BaseModel):
    success: Optional[bool] = True
    path: Optional[str] = None
    url: Optional[str] = None

class AnswerRequest(BaseModel):
    q: Optional[str] = None
    username: Optional[str] = None

class GenQuizRequest(BaseModel):
    theme: Optional[str] = Field(..., max_length=100)
    amount: Optional[int] = 100

class GenQuizResponse(BaseModel):
    success: Optional[bool] = True
    question: Optional[str] = ""
    alternatives: Optional[List[str]] = []
    truth: Optional[int] = -1
    voice_url: Optional[AnyUrl] = None

class VectorFilterRequest(BaseModel):
    filter: dict = {}
    sort: Optional[dict] = {"_id": -1}
    skip: Optional[int] = 0
    limit: Optional[int] = 100

class VectorDeleteRequest(BaseModel):
    ids: List[str]

class VectorDeleteResponse(BaseModel):
    success: Optional[bool] = True

class VectorUsernamesDeleteRequest(BaseModel):
    usernames: List[str]

class VectorUsernamesDeleteResponse(BaseModel):
    success: Optional[bool] = True
