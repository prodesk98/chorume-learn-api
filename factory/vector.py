from typing import Dict, Union, List

from models import (
    Vector, SelectVectorFactoryRequest, AllVectorFactoryRequest,
    AllDeleteVectorFactoryRequest
)

from databases import AsyncMongo, Mongo

class VectorFactory:
    def __init__(self):
        self.vector = Vector()
        self.asyncmongo = AsyncMongo('vectors')
        self.mongo = Mongo('vectors')

    def dump(self) -> Dict:
        return self.vector.model_dump()

    @staticmethod
    def load(vec: Dict) -> Vector:
        return Vector(**vec)

    async def aget(self, request: SelectVectorFactoryRequest) -> Union[Vector, None]:
        result = await self.asyncmongo.select(request.filter)
        if result is None:
            return result
        self.vector = self.load(result)
        return self.vector

    async def afind_all(self, request: AllVectorFactoryRequest) -> List[Vector]:
        result = await self.asyncmongo.all(
            filter=request.filter,
            sort=request.sort,
            skip=request.skip,
            limit=request.limit
        )
        return [self.load(vec) for vec in result]

    async def adelete_all(self, request: AllDeleteVectorFactoryRequest) -> None:
        await self.asyncmongo.delete(request.ids)

    async def acreate(self, request: List[Vector]) -> None:
        await self.asyncmongo.insert(documents=[vec.model_dump() for vec in request])

    def create(self, request: List[Vector]) -> None:
        self.mongo.insert(documents=[vec.model_dump() for vec in request])
