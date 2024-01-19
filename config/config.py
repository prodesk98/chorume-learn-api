from typing import Optional, List

from pydantic import BaseModel
from ujson import loads

configurations: dict
with open("config/config.json", "r") as rf:
    configurations = loads(rf.read())
    rf.close()

chorume: dict = configurations.get("chorume", {})
millionshow: dict = configurations.get("millionshow", {})
class Bot(BaseModel):
    chorume_personality: Optional[str] = chorume.get("personality", "")
    chorume_swear_words: Optional[List[str]] = chorume.get("swear_words", [])
    chorume_informal_greeting: Optional[List[str]] = chorume.get("informal_greeting", [])
    chorume_lang_context: Optional[str] = chorume.get("languages", {}).get("context", "")
    chorume_lang_language: Optional[str] = chorume.get("languages", {}).get("language", "")
    chorume_lang_answer: Optional[str] = chorume.get("languages", {}).get("answer", "")
    millionshow_discipline: Optional[str] = millionshow.get("discipline", "")
    millionshow_lang_topic: Optional[str] = millionshow.get("languages", {}).get("topic", "")
    millionshow_lang_context: Optional[str] = millionshow.get("languages", {}).get("context", "")
    millionshow_lang_alternatives: Optional[str] = millionshow.get("languages", {}).get("alternatives", "")
