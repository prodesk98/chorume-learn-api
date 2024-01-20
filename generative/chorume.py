import asyncio
from datetime import datetime
from langchain_community.callbacks import get_openai_callback
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from langchain.schema import (
    SystemMessage,
    HumanMessage,
)

from loguru import logger

from config import env

from provider import MilvusSearch

from config import bot


class AIChorume:
    def __init__(self, username: str):
        self.embeddings_model = OpenAIEmbeddings(
            model=env.OPENAI_EMBEDDING_MODEL,
            openai_api_key=env.OPENAI_API_KEY
        )
        self.username: str = username

    @staticmethod
    async def context(q: str) -> str:
        milvus = MilvusSearch()
        return "\n".join(["C%i: <%s>" % (i + 1, r.text.replace("\n", ""))
                          for i, r in enumerate(await milvus.asearch(query=q, k=2))])

    @staticmethod
    def llmChatOpenAI(temperature: float = 0.0) -> ChatOpenAI:
        return ChatOpenAI(
            temperature=temperature,
            model_name=env.OPENAI_CHAT_MODEL,
            openai_api_key=env.OPENAI_API_KEY,
            max_tokens=256
        )

    @property
    def swear_words(self) -> str:
        return "\n".join([f"- {sw}" for sw in bot.chorume_swear_words])

    @property
    def informal_greeting(self):
        return "\n".join([f"- {ig}" for ig in bot.chorume_informal_greeting])

    def current_time(self) -> str:
        hour = datetime.now().hour
        if 0 <= hour < 12:
            return f"Bom dia, {self.username}"
        elif 12 <= hour < 18:
            return f"Boa tarde, {self.username}"
        return f"Boa noite, {self.username}"

    @property
    def time(self) -> str:
        return "\"%s\". The current date is %s" % (self.current_time(), datetime.now().strftime("%d/%m/%Y às %H:%M"))

    @property
    def salutation(self) -> str:
        return f"Greet the user with {self.time}, informal words in the context of the answer, list below:\n{self.informal_greeting}"

    async def aquestion(self, q: str) -> str:
        messages = [
            SystemMessage(
                content=f"""{bot.chorume_personality}

Use swear words in the context of the answer, listed below:
{self.swear_words}

{self.salutation}

Use context to create an answer to the question.
The paragraphs in the context are separated by C<index>: <<context>>; format: C1: <context1>, C2: <context2>...
Context: \"\"\"{await self.context(q)}\"\"\"

context language: {bot.chorume_lang_context}.
language: {bot.chorume_lang_language}.
answer in language: {bot.chorume_lang_answer}.

respond with a maximum of 3 sentences."""
            ),
            HumanMessage(content=q),
        ]
        llm = self.llmChatOpenAI(temperature=.1)
        with get_openai_callback() as cb:
            response = await llm.ainvoke(input=messages)
            logger.info(f"LLM({env.OPENAI_CHAT_MODEL}); Cost US$%.5f; Tokens {cb.total_tokens}" % cb.total_cost)
        return response.content


if __name__ == "__main__":
    chorume = AIChorume("Choruminho")
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(chorume.aquestion("quem foi alan turing?")))