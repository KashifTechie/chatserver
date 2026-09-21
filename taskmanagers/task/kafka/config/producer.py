from taskmanagers.task.kafka.config.base import get_base_client_config
from django.conf import settings


def get_producer_config() -> dict:
    config = get_base_client_config("producer")

    config.update({
        "acks": settings.KAFKA_PRODUCER_ACKS,
        "enable.idempotence": settings.KAFKA_PRODUCER_ENABLE_IDEMPOTENCE,
        "retries": settings.KAFKA_PRODUCER_RETRIES,
        "delivery.timeout.ms": settings.KAFKA_PRODUCER_DELIVERY_TIMEOUT_MS,

        "linger.ms": settings.KAFKA_PRODUCER_LINGER_MS,
        "batch.size": settings.KAFKA_PRODUCER_BATCH_SIZE,
        "queue.buffering.max.messages": (
            settings.KAFKA_PRODUCER_QUEUE_MAX_MESSAGES
        ),
        "queue.buffering.max.kbytes": (
            settings.KAFKA_PRODUCER_QUEUE_MAX_KBYTES
        ),
        "statistics.interval.ms":(
            settings.STATISTICS_INTERVAL_MS   
        )
    })

    return config