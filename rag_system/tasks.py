from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task()
def store_rag_knowledge(rag_uuid):
    logger.info("The task is recieved")
    try:
        from rag_system.jobs.rag_storage import StoreRAG

        store = StoreRAG(rag_uuid=rag_uuid)
        store.initiate_rag_storage()
    except Exception as e:
        logger.info("Error occured while running the job: %s",str(e))

    