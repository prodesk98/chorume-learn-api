from typing import Optional, List
from pydantic import BaseModel
from orjson import loads
from pathlib import Path

configurations: dict
with open(f"{Path(__file__).resolve().parent}/config.json", "r") as rf:
    configurations = loads(rf.read())
    rf.close()

bot: dict = configurations.get("gen_bot", {})
quiz: dict = configurations.get("gen_quiz", {})
class Bot(BaseModel):
    bot_personality: Optional[str] = bot.get("personality", "")
    bot_swear_words: Optional[List[str]] = bot.get("swear_words", [])
    bot_informal_greeting: Optional[List[str]] = bot.get("informal_greeting", [])
    bot_lang_context: Optional[str] = bot.get("languages", {}).get("context", "")
    bot_lang_language: Optional[str] = bot.get("languages", {}).get("language", "")
    bot_lang_answer: Optional[str] = bot.get("languages", {}).get("answer", "")
    quiz_discipline: Optional[str] = quiz.get("discipline", "")
    quiz_lang_topic: Optional[str] = quiz.get("languages", {}).get("topic", "")
    quiz_lang_context: Optional[str] = quiz.get("languages", {}).get("context", "")
    quiz_lang_alternatives: Optional[str] = quiz.get("languages", {}).get("alternatives", "")
