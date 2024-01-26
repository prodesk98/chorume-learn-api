from datetime import datetime
from typing import List

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


class GenBot:
    def __init__(self, username: str):
        self.embeddings_model = OpenAIEmbeddings(
            model=env.OPENAI_EMBEDDING_MODEL,
            openai_api_key=env.OPENAI_API_KEY
        )
        self.username: str = username
        self.milvus = MilvusSearch()

    async def context(self, q: str, namespace: str = "default", k: int = 2) -> str:
        fetch = await self.milvus.asearch(query=q, k=k, ns=namespace)
        if len(fetch) == 0:
            return ""
        return ("The paragraphs in the context are separated by C<index>: <<context>>; "
                "format: C1: <context1>, C2: <context2>...\n\n%s") % "\n".join(
            ["C%i: <%s>" % (i + 1, r.text.replace("\n", ""))
             for i, r in enumerate(fetch)]
        )

    @staticmethod
    def llmChatOpenAI(temperature: float = 0.0) -> ChatOpenAI:
        return ChatOpenAI(
            temperature=temperature,
            model_name=env.OPENAI_CHAT_MODEL,
            openai_api_key=env.OPENAI_API_KEY,
            max_tokens=256
        )

    @staticmethod
    def swear_words(sw_list: List[str] = None) -> str:
        result = ("Use swear words in the context of the answer, listed below: \n%s" %
                "\n".join([f"- {sw}" for sw in (bot.bot_swear_words if sw_list is None else sw_list)]))
        if sw_list is not None:
            if len(sw_list) == 0:
                return ""
        return result

    @staticmethod
    def informal_greeting(ig_list: List[str] = None) -> str:
        return "\n".join([f"- {ig}" for ig in (bot.bot_informal_greeting if ig_list is None else ig_list)])

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


    def salutation(self, ig_list: List[str] = None) -> str:
        result = f"Greet the user with {self.time}, informal words in the context of the answer, list below:\n{self.informal_greeting(ig_list)}"
        if ig_list is not None:
            if len(ig_list) == 0:
                return ""
        return result

    async def generate(self, q: str, namespace: str = "default", personality: str = None,
                       swear_words: List[str] = None, informal_greeting: List[str] = None) -> str:

        messages = [
            SystemMessage(
                content=f"""{bot.bot_personality if personality is None else personality}

{self.swear_words(swear_words)}

{self.salutation(informal_greeting)}

Use context to create an answer to the question.
Only use the context that is related to the user's question.
Context: \"\"\"{await self.context(q, namespace, 2)}\"\"\"

context language: {bot.bot_lang_context}.
language: {bot.bot_lang_language}.
answer in language: {bot.bot_lang_answer}.

Output with a maximum of 3 sentences."""
            ),
            HumanMessage(content=q),
        ]
        llm = self.llmChatOpenAI(temperature=.1)
        print(messages[0].content)
        with get_openai_callback() as cb:
            response = await llm.ainvoke(input=messages)
            logger.info(f"LLM({env.OPENAI_CHAT_MODEL}); Cost US$%.5f; Tokens {cb.total_tokens}" % cb.total_cost)
        return response.content
