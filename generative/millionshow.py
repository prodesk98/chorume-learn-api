import asyncio
import re
from typing import Dict, Union, List

import aiofiles
from aiohttp import ClientSession
from langchain_community.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI
from loguru import logger

from config import env
from models import ShowMillionResponse

from langchain.schema import SystemMessage

from json import loads, JSONDecodeError

from provider import MilvusSearch

from random import shuffle

from pydub import AudioSegment
from pathlib import Path

import shutil

class ShowMillion:
    def __init__(self, theme: str, amount: int):
        self.theme = theme
        self.amount = amount

    @staticmethod
    async def context(q: str) -> str:
        milvus = MilvusSearch()
        return "\n".join(["C%i: <%s>" % (i+1, r.text.replace("\n", ""))
                          for i, r in enumerate(await milvus.asearch(query=q, k=2))])

    @staticmethod
    def llmChatOpenAI(temperature: float = 0.0) -> ChatOpenAI:
        return ChatOpenAI(
            temperature=temperature,
            model_name=env.OPENAI_MILLION_SHOW_MODEL,
            openai_api_key=env.OPENAI_API_KEY,
            max_tokens=150,
            model_kwargs={
                "response_format": {
                    "type": "json_object"
                }
            }
        )

    @staticmethod
    def marshal(content: str) -> Dict:
        def normalize_json(dictionary) -> Dict:
            for key, value in dictionary.items():
                if isinstance(value, str):
                    dictionary[key] = value.replace("\n", "")
                elif isinstance(value, list):
                    dictionary[key] = [item.replace("\n", "") if isinstance(item, str) else item for item in value]
            return dictionary

        try:
            return loads(content, object_hook=normalize_json, parse_float=float)
        except JSONDecodeError as e:
            logger.error(e)
        return {}

    @staticmethod
    def build(quiz: dict) -> Dict:
        question: Union[str, None] = quiz.get("question", None)
        if question is None:
            return {}
        truth: Union[str, None] = quiz.get("truth", None)
        if truth is None:
            return {}
        qz: List[str] = quiz.get("alternatives", [])
        if not qz:
            return {}

        # busca o padrão → id) questão
        pattern = re.compile(r"([a-d])\)\s*(.*)")
        alternatives: List[str] = []
        for q in qz:
            sp = re.findall(pattern, q)
            for k, v in sp:
                alternatives.append(v.strip())

        # se não listou 4
        if len(alternatives) < 4:
            return {}

        # transforma o id) em indexe
        truth_integer: int = {
            "a": 0,
            "b": 1,
            "c": 2,
            "d": 3
        }.get(truth, 99)

        try:
            # salva a resposta correta
            right: str = alternatives[truth_integer]
        except IndexError:
            return {}

        # embaralha as questões
        shuffle(alternatives)

        # recalcula a resposta correta
        truth_result: int = alternatives.index(right) + 1

        # retorna o modelo pronto
        return dict(
            question=question,
            truth=truth_result,
            alternatives=alternatives
        )

    @staticmethod
    def mix_audio(absolute_path: str) -> Path:
        sm_sound = AudioSegment.from_file("audios/show_million.mp3")
        gen_sound = AudioSegment.from_file(absolute_path)
        comb_sound = sm_sound + gen_sound
        comb_sound.export(absolute_path, format="mp3")

        return Path(absolute_path)

    async def voice(self, quiz: dict) -> Union[str, None]:
        alternatives: List[str] = quiz.get('alternatives', [])
        presentation = f"""A pergunta vale {self.amount} coins.

{quiz.get("question")}

Resposta A, {alternatives[0]}.
Resposta B, {alternatives[1]}.
Resposta C, {alternatives[2]}.
Resposta D, {alternatives[3]}.""".replace("\n", " ")

        presentation = " ".join(presentation.split())
        async with ClientSession() as sess:
            async with sess.post(f"https://api.elevenlabs.io/v1/text-to-speech/{env.MILLION_SHOW_VOICE_ID}/stream", json={
                "model_id": "eleven_multilingual_v2",
                "text": presentation,
                "voice_settings": {
                    "similarity_boost": 1,
                    "stability": 1,
                    "style": 1,
                    "use_speaker_boost": True
                }
            }, headers={"Content-Type": "application/json", "xi-api-key": env.ELEVENLABS_API_KEY}) as response:
                if response.status == 200:
                    chunk_size = 8192 # 8 KB
                    async with aiofiles.tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        async with aiofiles.open(temp_file.name, "wb") as file:
                            async for chunk in response.content.iter_chunked(chunk_size):
                                await file.write(chunk)
                            await file.close()
                        await temp_file.close()
                    file_mp3 = f"{temp_file.name}.mp3"
                    shutil.move(temp_file.name, file_mp3)
                    sound: Path = await asyncio.to_thread(self.mix_audio, file_mp3)
                    return f"{env.LEARN_FRONT_END}/files/{sound.absolute().name.split('/')[-1]}"
        return None

    async def generate(self) -> ShowMillionResponse:
        messages = [
            SystemMessage(content=f"""You are a Quizzes Game (Quiz Show) generator related to technology and programming.
Use the topic and the context as a reference to generate the question and the alternatives.
The context and the topic only as a reference.
Write (1)one questionnaire with (4)four alternatives: a, b, c, and d.
The questionnaire with just (1)one sentence, and the alternatives with only (5)five words at most.

Topic: \"\"\"{self.theme}\"\"\"

The paragraphs in the context are separated by C<index>: <<context>>; format: C1: <context1>, C2: <context2>...
Context: \"\"\"{await self.context(self.theme)}\"\"\"

JSON format:
{{"question":"<question>","truth":"<truth>","alternatives":["a) <a>","b) <b>","c) <c>","d) <d>"]}}

JSON Example:
{{"question":"<quiz>","truth":"<a|b|c|d>","alternatives":["a) <Alternative A>","b) <Alternative B>","c) <Alternative C>","d) <Alternative D>"]}}

JSON Schema:
question: the quiz question.
truth: the letter of the correct alternative.
alternatives: list of alternatives based on the correct format: a) <a>, b) <b>, c) <c>, d) <d>

Topic language: Portuguese (Brazil).
Context language: Portuguese (Brazil).
Alternatives in language: Portuguese (Brazil).

Output in JSON.""")
        ]

        llm = self.llmChatOpenAI(temperature=0)
        with get_openai_callback() as cb:
            response = await llm.ainvoke(input=messages)
            logger.info(f"LLM({env.OPENAI_MILLION_SHOW_MODEL}); Cost US$%.5f; Tokens {cb.total_tokens}" % cb.total_cost)

        quiz = await asyncio.to_thread(self.marshal, response.content)
        quiz_parsed: dict = await asyncio.to_thread(self.build, quiz)

        if not quiz_parsed:
            return ShowMillionResponse()

        if env.MILLION_SHOW_VOICE_ENABLED is True:
            quiz_parsed.update({
                "voice_url": await self.voice(quiz_parsed)
            })

        return ShowMillionResponse(**quiz_parsed)
