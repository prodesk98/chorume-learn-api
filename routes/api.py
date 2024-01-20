from typing import List
from config import env
from provider import MilvusSearch, Voice
from security import validate_token
from tasks import upsert as TaskUpsert
from generative import AIChorume, ShowMillion
from models import (
    UpsertResponse, UpsertRequest, QueryResponse,
    AnswerResponse, AnswerRequest, TextToVoiceResponse,
    TextToVoiceRequest, VoicePlayRequest, VoicePlayResponse,
    MillionShowResponse, MillionShowRequest, Vector,
    VectorFilterRequest, AllVectorFactoryRequest, VectorDeleteRequest,
    AllDeleteVectorFactoryRequest, VectorDeleteResponse, VectorUsernamesDeleteRequest,
    VectorUsernamesDeleteResponse
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
    response_model=UpsertResponse
)
def upsert(request: UpsertRequest = Body(...)):
    try:
        job = TaskUpsert.delay(request.model_dump())

        logger.info(f"[{job.id}] upsert job queued successfully.")
        return UpsertResponse()
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@api.get(
    "/semantic-search",
    response_model=QueryResponse
)
async def semantic_search(q = Query("", title="query", max_length=50)):
    try:
        stime = time()
        milvus = MilvusSearch()
        responses = await milvus.asearch(query=q)

        if env.DEBUG:
            logger.debug(f"Semantic search was executed successfully; time: {time() - stime}")

        return QueryResponse(
            responses=[
                {
                    "id": resp.id,
                    "text": resp.text
                } for resp in responses
            ]
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@api.post(
    "/asking",
    response_model=AnswerResponse
)
async def asking(request: AnswerRequest):
    try:
        stime = time()
        gen = AIChorume(request.username)
        response = await gen.aquestion(request.q)

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
    response_model=TextToVoiceResponse
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
    "/voice-playback-queue",
    response_model=VoicePlayResponse
)
async def voice_play(request: VoicePlayRequest):
    if request.channel_id is None:
        return VoicePlayResponse(
            success=False
        )
    return VoicePlayResponse()

@api.post(
    "/million-show",
    response_model=MillionShowResponse
)
async def million_show(request: MillionShowRequest):
    if request.theme is None:
        return MillionShowResponse(
            success=False
        )
    try:
        stime = time()
        millionShowResponse = await ShowMillion(
            theme=request.theme, amount=request.amount).generate()

        if env.DEBUG:
            logger.debug(f"Quiz generated successfully; time: {time() - stime}")

        return MillionShowResponse(
            question=millionShowResponse.question,
            alternatives=millionShowResponse.alternatives,
            truth=millionShowResponse.truth,
            voice_url=millionShowResponse.voice_url
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@api.post(
    "/vectors",
    response_model=List[Vector]
)
async def create_vector(request: VectorFilterRequest):
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
    response_model=VectorDeleteResponse
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
    response_model=VectorUsernamesDeleteResponse
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
