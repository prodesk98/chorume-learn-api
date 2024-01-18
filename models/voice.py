from typing import Optional

from pydantic import BaseModel, AnyUrl


class Audio(BaseModel):
    success: Optional[bool] = False
    absolute_path: Optional[str] = None

class VoicePlayRequest(BaseModel):
    channel_id: Optional[str] = None
    audio: AnyUrl

class VoicePlayResponse(BaseModel):
    success: Optional[bool] = True
