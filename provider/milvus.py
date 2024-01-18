from typing import List

import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pymilvus import connections, db, Collection, Hits

from models import UpsertTasksDocument, DocumentTasksSearch, Vector

from schemas import MilvusSchema

from langchain_openai import OpenAIEmbeddings

from config import env

from hashlib import md5

from loguru import logger

from factory import VectorFactory

connections.connect(
    alias="default",
    host=env.MILVUS_HOST,
    port=env.MILVUS_PORT
)

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

    async def asearch(self, query: str, k: int = 3) -> List[DocumentTasksSearch]:
        try:
            embedding = await self.aembedding(query)
            self.collection.load()
            SearchResult = self.collection.search(
                **dict(
                    data=[embedding],
                    anns_field="embedding",
                    param={
                        "metric_type": "L2",
                        'index_type': "IVF_FLAT",
                        "offset": 0,
                        "ignore_growing": False,
                        "params": {
                            "nlist": 2048
                        }
                    },
                    limit=k,
                    output_fields=['text'],
                )
            )
            result: Hits = SearchResult[0]
            if len(result.ids) == 0:
                return []
            return [DocumentTasksSearch(text=hit.entity.get('text')) for hit in result]
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
        self.documents: List[Vector] = []

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
        collection.create_index(field_name="embedding", index_params={
            'metric_type': 'L2',
            'index_type': "IVF_FLAT",
            'params': {
                "nlist": 2048
            }
        })
        return collection

    def upsert(self, document: UpsertTasksDocument) -> bool:
        documents = self.split_text(content=document.content)
        ids = [md5(doc.encode()).hexdigest() for doc in documents]
        embeddings = self.embeddings_documents(documents=documents)

        for i, doc in enumerate(documents):
            self.documents.append(
                Vector().create(
                    id=ids[i],
                    content=doc,
                    created_by=document.username,
                )
            )

        UpsertResult = self.collection.upsert(
            data=[
                ids,
                documents,
                embeddings,
            ]
        )

        self.vectorFactory.create(request=self.documents)

        logger.info(f"Upsert count: {UpsertResult.upsert_count}; errors: {UpsertResult.err_count}; "
                    f"success percentage: {UpsertResult.succ_count / UpsertResult.insert_count * 100}")

        return UpsertResult.succ_count > 0


if __name__ == "__main__":
    mds = MilvusDataStore()