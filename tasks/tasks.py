from celery import Celery

from config import env

from models import UpsertTasksDocument

from provider import MilvusDataStore

celery = Celery(
    broker=env.AMQP_DSN,
    backend=None,
    broker_connection_retry_on_startup=True
)


@celery.task(name="upsert", autoretry_for=(Exception,), retry_backoff=3)
def upsert(data: dict) -> bool:
    """
    upsert vetores
    :return:
    """
    datastore = MilvusDataStore()
    return datastore.upsert(document=UpsertTasksDocument(**data))
