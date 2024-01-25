from typing import List, Dict, Union
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import MongoClient
from pymongo.collection import Collection

from config import env

class Mongo:
    def __init__(self, collection: str):
        self.client = MongoClient(env.MONGO_DSN)
        self.collection: Collection = self.client[env.MONGO_DB_NAME][collection]

    def insert(self, documents: List[dict]) -> None:
        with self.client.start_session() as s:
            self.collection.insert_many(documents, session=s)


class AsyncMongo:
    def __init__(self, collection: str):
        self.client = AsyncIOMotorClient(env.MONGO_DSN)
        self.collection: AsyncIOMotorCollection = self.client[env.MONGO_DB_NAME][collection]

    async def all(self, filter: dict = None, sort: dict = None, skip: int = 0, limit: int = 100) -> List[Dict]:
        if filter is None:
            filter = {}
        if sort is None:
            sort = {"_id": -1}
        result: List[dict] = []
        async with await self.client.start_session() as s:
            async for doc in self.collection.find(filter, session=s).sort(
                sort
            ).skip(skip).limit(limit):
                result.append(doc)
        return result

    async def select(self, filter: dict = None) -> Union[Dict, None]:
        if filter is None:
            filter = {}
        async with await self.client.start_session() as s:
            return await self.collection.find_one(filter, session=s)

    async def insert(self, documents: List[dict]) -> None:
        async with await self.client.start_session() as s:
            await self.collection.insert_many(documents, session=s)

    async def update(self, documents: List[dict], filter: dict = None) -> None:
        if filter is None:
            filter = {}
        async with await self.client.start_session() as s:
            await self.collection.update_many(
                filter, update=[{"$set": doc} for doc in documents], upsert=True, session=s)

    async def delete(self, ids: List[str]) -> None:
        async with await self.client.start_session() as s:
            async with s.start_transaction():
                for id in ids:
                    await self.collection.delete_one(
                        {
                            "$or":[
                                {"id": id},
                                {"_id": id}
                            ]
                        }
                    )
