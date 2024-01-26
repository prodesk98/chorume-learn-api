from typing import List
from config import env
from provider import MilvusSearch, Voice
from security import validate_token
from tasks import upsert as task_learn_upsert
from generative import GenBot, GenQuiz
from models import (
    UpsertResponse, UpsertRequest, QueryResponse,
    AnswerResponse, AnswerRequest, TextToVoiceResponse,
    GenQuizResponse, GenQuizRequest, Vector,
    VectorFilterRequest, AllVectorFactoryRequest, VectorDeleteRequest,
    AllDeleteVectorFactoryRequest, VectorDeleteResponse, VectorUsernamesDeleteRequest,
    VectorUsernamesDeleteResponse, TextToVoiceRequest
)
from loguru import logger
from fastapi import Depends, HTTPException, Body, Query, APIRouter
from time import time
from factory import VectorFactory


api = APIRouter(
    prefix="/api",
    dependencies=[Depends(validate_token)],
)

@api.post(
    "/upsert",
    response_model=UpsertResponse,
    summary="Teach the robot",
    description="Upload content to the vector database."
)
def upsert(request: UpsertRequest = Body(...)):
    try:
        job = task_learn_upsert.delay(request.model_dump())

        logger.info(f"[{job.id}] upsert job queued successfully.")
        return UpsertResponse()
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@api.get(
    "/semantic-search",
    response_model=QueryResponse,
    summary="Retrieve a list of contexts",
    description="Retrieve a list of content from the vector database."
)
async def semantic_search(q = Query(..., title="query", max_length=50), ns = Query("default", title="namespace", max_length=32)):
    try:
        stime = time()
        milvus = MilvusSearch()
        responses = await milvus.asearch(query=q, ns=ns)

        if env.DEBUG:
            logger.debug(f"Semantic search was executed successfully; time: {time() - stime}")

        return QueryResponse(
            responses=[
                {
                    "id": resp.id,
                    "text": resp.text,
                    "namespace": resp.namespace
                } for resp in responses
            ]
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@api.post(
    "/asking",
    response_model=AnswerResponse,
    summary="Get a response from the robot",
    description="Retrieve a response from the GPT model, using the context from the vector database."
)
async def asking(request: AnswerRequest):
    try:
        stime = time()
        gen = GenBot(request.username)
        response = await gen.generate(
            q=request.q,
            namespace=request.namespace,
            personality=request.personality,
            swear_words=request.swear_words,
            informal_greeting=request.informal_greeting
        )

        if env.DEBUG:
            logger.debug(f"question answered successfully; time: {time() - stime}")

        return AnswerResponse(
            response=response
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@api.post(
    "/text-to-speech",
    response_model=TextToVoiceResponse,
    summary="Text to Speech",
    description="Transcribe a text to audio."
)
async def text_to_speech(request: TextToVoiceRequest):
    if not env.LEARN_VOICE_ENABLED:
        return TextToVoiceResponse(
            success=False
        )
    try:
        stime = time()
        voice = Voice(request)
        audio = await voice.text_to_voice()

        if audio.absolute_path is None:
            raise HTTPException(status_code=500, detail="Unable to transform text into audio.")

        if env.DEBUG:
            logger.debug(f"text converted to audio executed successfully; time: {time() - stime}")

        return TextToVoiceResponse(
            path=audio.absolute_path,
            url=f"{env.LEARN_FRONT_END}/files/{audio.absolute_path.split('/')[-1]}"
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@api.post(
    "/questionnaire",
    response_model=GenQuizResponse,
    summary="Generate a questionnaire",
    description="Generate a questionnaire with alternatives using the GPT model with context."
)
async def questionnaire(request: GenQuizRequest):
    if request.theme is None:
        return GenQuizResponse(
            success=False
        )
    try:
        stime = time()
        quiz = await GenQuiz(theme=request.theme, amount=request.amount).generate(request.namespace)

        if env.DEBUG:
            logger.debug(f"Quiz generated successfully; time: {time() - stime}")

        return GenQuizResponse(
            question=quiz.question,
            alternatives=quiz.alternatives,
            truth=quiz.truth,
            voice_url=quiz.voice_url
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@api.post(
    "/vectors",
    response_model=List[Vector],
    summary="Retrieve a list of vectors",
    description="Retrieve a list of vectors from the NoSQL database"
)
async def vectors_fetch(request: VectorFilterRequest):
    try:
        return await VectorFactory().afind_all(
            AllVectorFactoryRequest(
                filter=request.filter,
                sort=request.sort,
                skip=request.skip,
                limit=request.limit
            )
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@api.delete(
    "/vectors",
    response_model=VectorDeleteResponse,
    summary="Delete vectors",
    description="Delete a set of vectors using IDs."
)
async def delete_vectors_by_ids(request: VectorDeleteRequest):
    try:
        await VectorFactory().adelete_all(request=AllDeleteVectorFactoryRequest(ids=request.ids))
        await MilvusSearch().adelete(ids=request.ids)

        return VectorDeleteResponse()
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@api.delete(
    "/vectors/usernames",
    response_model=VectorUsernamesDeleteResponse,
    summary="Delete vectors by usernames",
    description="Delete a set of vectors using by usernames."
)
async def delete_vectors_by_username(request: VectorUsernamesDeleteRequest):
    try:
        vectors = [
            _ for username in request.usernames
            for _ in await VectorFactory().afind_all(
                AllVectorFactoryRequest(
                    filter={"created_by": username},
                    sort={"_id": -1},
                    skip=0,
                    limit=250
                )
            )
        ]
        if len(vectors) == 0:
            return VectorUsernamesDeleteResponse()

        ids: List[str] = [
            vec.id for vec in vectors
        ]

        await VectorFactory().adelete_all(request=AllDeleteVectorFactoryRequest(ids=ids))
        await MilvusSearch().adelete(ids=ids)

        return VectorUsernamesDeleteResponse()
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")
