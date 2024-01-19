from pymilvus import db, connections, Collection, utility

from dotenv import load_dotenv
from os import getenv

from schemas.milvus_schema import Schema

load_dotenv()


MILVUS_DB_NAME = getenv("MILVUS_DB_NAME")
MILVUS_COLLECTION_NAME = getenv("MILVUS_COLLECTION_NAME")
MILVUS_HOST = getenv("MILVUS_HOST")
MILVUS_PORT = int(getenv("MILVUS_PORT"))

if not isinstance(MILVUS_HOST, str):
    raise ValueError("MILVUS_HOST is not defined in .env")

if not isinstance(MILVUS_PORT, int):
    raise ValueError("MILVUS_PORT is not defined in .env or Type Value is not integer")

connections.connect(
    alias="default",
    host=MILVUS_HOST,
    port=MILVUS_PORT
)

if MILVUS_DB_NAME not in db.list_database():
    db.create_database(MILVUS_DB_NAME)

print(f"List databases: {db.list_database()}")

db.using_database("knowledge")

collection = Collection(name=MILVUS_COLLECTION_NAME, schema=Schema)
collection.create_index(field_name="embedding", index_params={
    'metric_type': 'COSINE',
    'index_type': "IVF_FLAT",
    'params': {"nlist": 128}
})

if not utility.has_collection(MILVUS_COLLECTION_NAME):
    utility.index_building_progress(MILVUS_COLLECTION_NAME)
    print("Milvus databases created successfully!")

print("Milvus is already built.")

from loguru import logger
try:
    import provider
    import databases
except ImportError as e:
    logger.error(e)