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
        return await asyncio.to_thread(self.delete, ids)

    def search(self, data: dict) -> SearchResult:
        return self.collection.search(**data)

    def delete(self, ids: List[str]) -> None:
        try:
            self.collection.delete(
                expr=f"id in {str(ids)}"
            )
        except Exception as e:
            logger.error(e)

    async def asearch(self, query: str, k: int = 3, ns: str = "default") -> List[DocumentTasksSearch]:
        try:
            embedding = await self.aembedding(query)
            search_result = await asyncio.to_thread(
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
                    expr=f"ns == \"{ns}\"",
                    limit=k,
                    output_fields=['id', 'text', 'ns'],
                )
            )
            result: Hits
            for result in search_result:
                return [
                    DocumentTasksSearch(
                        id=hit.entity.get('id'),
                        text=hit.entity.get('text'),
                        namespace=hit.entity.get('ns')
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
        self.collection.load()
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

    def upsert(self, document: UpsertTasksDocument) -> bool:
        documents = self.split_text(content=document.content)
        if len(documents) == 0:
            raise ValueError("Unable to load documents")

        embeddings = self.embeddings_documents(documents=documents)
        if len(embeddings) == 0:
            raise ValueError("Unable to load embeds")

        ids = [md5(doc.encode()).hexdigest() for doc in documents]
        ns = [document.namespace for _ in ids]

        self.vectors = [
            Vector().create(
                id=ids[i],
                content=doc,
                created_by=document.username,
                namespace=document.namespace
            ) for i, doc in enumerate(documents)
        ]

        upsert_result = self.collection.upsert(
            data=[
                ids,
                documents,
                ns,
                embeddings,
            ]
        )

        self.vectorFactory.create(request=self.vectors)

        logger.info(f"Upsert count: {upsert_result.upsert_count}; errors: {upsert_result.err_count}; "
                    f"success percentage: {upsert_result.succ_count / upsert_result.insert_count * 100}")

        return upsert_result.succ_count > 0
