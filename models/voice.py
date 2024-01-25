from typing import Optional
from pydantic import BaseModel


class Audio(BaseModel):
    success: Optional[bool] = False
    absolute_path: Optional[str] = None
