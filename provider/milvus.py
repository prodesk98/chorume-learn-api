import asyncio
from typing import List

import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pymilvus import connections, db, Collection, Hits, SearchResult

from models import UpsertTasksDocument, DocumentTasksSearch, Vector

from schemas import MilvusSchema

from langchain_openai import OpenAIEmbeddings

from config import env

from hashlib import md5

from loguru import logger

from factory import VectorFactory


class MilvusSearch:
    def __init__(self):
        if not db.connections.has_connection("default"):
            connections.connect(
                alias="default",
                host=env.MILVUS_HOST,
                port=env.MILVUS_PORT
            )
        db.using_database(env.MILVUS_DB_NAME)

        self.collection = self.get_collection()
        self.collection.load()
        self.embeddings_model = OpenAIEmbeddings(
            model=env.OPENAI_EMBEDDING_MODEL,
            openai_api_key=env.OPENAI_API_KEY
        )

    @staticmethod
    def get_collection() -> Collection:
        return Collection(
            name=env.MILVUS_COLLECTION_NAME,
            schema=MilvusSchema,
        )

    async def aembedding(self, query: str) -> List[float]:
        return await self.embeddings_model.aembed_query(query)

    async def adelete(self, ids: List[str]) -> None:
        try:
            self.collection.delete(
                expr="id in [%s]" % (f"{_id}," for _id in ids)
            )
        except Exception as e:
            logger.error(e)

    def search(self, data: dict) -> SearchResult:
        return self.collection.search(**data)

    async def asearch(self, query: str, k: int = 3) -> List[DocumentTasksSearch]:
        try:
            embedding = await self.aembedding(query)
            searchResult = await asyncio.to_thread(
                self.search,
                dict(
                    data=[embedding],
                    anns_field="embedding",
                    param={
                        "metric_type": "COSINE",
                        'index_type': "IVF_FLAT",
                        "params": {
                            "nprobe": 12
                        }
                    },
                    limit=k,
                    output_fields=['id', 'text'],
                )
            )
            result: Hits
            for result in searchResult:
                return [
                    DocumentTasksSearch(
                        id=hit.entity.get('id'),
                        text=hit.entity.get('text'),
                    ) for hit in result
                ]
        except Exception as err:
            logger.error(err)
            return []

class MilvusDataStore:
    def __init__(self):
        if not db.connections.has_connection("default"):
            connections.connect(
                alias="default",
                host=env.MILVUS_HOST,
                port=env.MILVUS_PORT
            )
        db.using_database(env.MILVUS_DB_NAME)

        self.collection = self.get_collection()
        self.tokenizer = tiktoken.encoding_for_model(model_name=env.OPENAI_EMBEDDING_MODEL)
        self.embeddings_model = OpenAIEmbeddings(
            model=env.OPENAI_EMBEDDING_MODEL,
            openai_api_key=env.OPENAI_API_KEY
        )
        self.vectorFactory = VectorFactory()
        self.vectors: List[Vector] = []

    def _tokenizer(self, text: str) -> int:
        tokens = self.tokenizer.encode(
            text=text,
            disallowed_special=()
        )
        return len(tokens)

    def split_text(self, content: str, chunk_size: int = 100, chunk_overlap: int = 20) -> List[str]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self._tokenizer,
            separators=["\n\n", "\n", " ", ""]
        )
        return text_splitter.split_text(content)

    def embeddings_documents(self, documents: List[str]) -> List[List[float]]:
        return self.embeddings_model.embed_documents(documents)

    @staticmethod
    def get_collection() -> Collection:
        collection = Collection(name=env.MILVUS_COLLECTION_NAME, schema=MilvusSchema)
        collection.create_index(
            field_name="embedding",
            index_params={
                'metric_type': 'COSINE',
                'index_type': "IVF_FLAT",
                'params': {
                    "nlist": 128
                }
            }
        )
        return collection

    def score(self, embedding: List[List[float]]) -> List[float]:
        searchResult = self.collection.search(
            **dict(
                data=embedding,
                anns_field="embedding",
                param={
                    "metric_type": "COSINE",
                    'index_type': "IVF_FLAT",
                    "params": {
                        "nprobe": 12
                    }
                },
                limit=1,
                output_fields=[],
            )
        )
        results: List[float] = []
        result: Hits

        for result in searchResult:
            results.extend(result.distances)
        return results

    def upsert(self, document: UpsertTasksDocument) -> bool:
        documents = self.split_text(content=document.content)
        embeddings = self.embeddings_documents(documents=documents)

        valid_documents: List[str] = []
        valid_embeddings: List[List[float]] = []
        # removes duplicate documents using the similarity score
        for k, score in enumerate(self.score(embeddings)):
            if score <= 0.99:
                valid_documents.append(documents[k])
                valid_embeddings.append(embeddings[k])

        ids = [md5(valid_doc.encode()).hexdigest() for valid_doc in valid_documents]

        if len(ids) == 0:
            return False

        self.vectors = [
            Vector().create(
                id=ids[i],
                content=doc,
                created_by=document.username,
            ) for i, doc in enumerate(valid_documents)
        ]

        UpsertResult = self.collection.upsert(
            data=[
                ids,
                valid_documents,
                valid_embeddings,
            ]
        )

        self.vectorFactory.create(request=self.vectors)

        logger.info(f"Upsert count: {UpsertResult.upsert_count}; errors: {UpsertResult.err_count}; "
                    f"success percentage: {UpsertResult.succ_count / UpsertResult.insert_count * 100}")

        return UpsertResult.succ_count > 0


if __name__ == "__main__":
    mds = MilvusDataStore()