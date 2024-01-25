from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, MongoDsn, AmqpDsn, AnyHttpUrl
from os import getenv
from .config import Bot
load_dotenv()

class Settings(BaseModel):
    LEARN_VERSION: Optional[str] = getenv("LEARN_VERSION", "0.0.1")
    LEARN_TOKEN: Optional[str] = getenv("LEARN_TOKEN", None)
    OPENAI_API_KEY: Optional[str] = getenv("OPENAI_API_KEY", None)
    OPENAI_CHAT_MODEL: Optional[str] = getenv("OPENAI_CHAT_MODEL", "gpt-3.5-turbo-1106")
    OPENAI_EMBEDDING_MODEL: Optional[str] = getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
    OPENAI_QUIZ_MODEL: Optional[str] = getenv("OPENAI_QUIZ_MODEL", "gpt-4-1106-preview")
    AMQP_DSN: Optional[AmqpDsn] = getenv("AMQP_DSN", "pyamqp://guest:guest@rabbitmq:5672//")
    MONGO_DSN: Optional[MongoDsn] = getenv("MONGO_DSN", "mongodb://root:default@mongo:27017")
    MONGO_DB_NAME: Optional[str] = getenv("MONGO_DB_NAME", "learn")
    MILVUS_HOST: Optional[str] = getenv("MILVUS_HOST", "standalone")
    MILVUS_PORT: Optional[int] = getenv("MILVUS_PORT", 19530)
    MILVUS_DB_NAME: Optional[str] = getenv("MILVUS_DB_NAME", "knowledge")
    MILVUS_COLLECTION_NAME: Optional[str] = getenv("MILVUS_COLLECTION_NAME", "brain")
    ELEVENLABS_API_KEY: Optional[str] = getenv("ELEVENLABS_API_KEY", None)
    ASKING_VOICE_ID: Optional[str] = getenv("ASKING_VOICE_ID", None)
    ASKING_VOICE_ENABLED: Optional[bool] = (getenv("ASKING_VOICE_ENABLED", "true") == "true")
    QUIZ_VOICE_ID: Optional[str] = getenv("QUIZ_VOICE_ID", None)
    QUIZ_VOICE_ENABLED: Optional[bool] = (getenv("QUIZ_VOICE_ENABLED", "true") == "true")
    LEARN_FRONT_END: Optional[AnyHttpUrl] = getenv("LEARN_FRONT_END", "http://localhost:3001")
    DEBUG: Optional[bool] = (getenv("DEBUG", "true") == "true")

env = Settings()
bot = Bot()
