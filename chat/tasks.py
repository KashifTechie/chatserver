from celery import shared_task

@shared_task
def process_message(conversation_id, sender_id, message):
    from .job.process_message_job import process_message_job
    process_message_job(conversation_id, sender_id, message)