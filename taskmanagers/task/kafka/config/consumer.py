from django.conf import settings

from kafka.config.base import get_base_client_config


def get_consumer_config(group_id: str) -> dict:
    config = get_base_client_config("consumer")

    config.update({
        "group.id": group_id,

        "auto.offset.reset": settings.KAFKA_CONSUMER_AUTO_OFFSET_RESET,

        "enable.auto.commit": (
            settings.KAFKA_CONSUMER_ENABLE_AUTO_COMMIT
        ),

        "session.timeout.ms": (
            settings.KAFKA_CONSUMER_SESSION_TIMEOUT_MS
        ),

        "heartbeat.interval.ms": (
            settings.KAFKA_CONSUMER_HEARTBEAT_INTERVAL_MS
        ),

        "max.poll.interval.ms": (
            settings.KAFKA_CONSUMER_MAX_POLL_INTERVAL_MS
        ),

        "fetch.min.bytes": (
            settings.KAFKA_CONSUMER_FETCH_MIN_BYTES
        ),

        "fetch.max.bytes": (
            settings.KAFKA_CONSUMER_FETCH_MAX_BYTES
        ),

        "fetch.wait.max.ms": (
            settings.KAFKA_CONSUMER_FETCH_WAIT_MAX_MS
        ),
    })

    return config