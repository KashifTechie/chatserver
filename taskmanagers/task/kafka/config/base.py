from django.conf import settings


def get_base_client_config(client_type: str) -> dict:
    config = {
        "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "client.id": f"{settings.KAFKA_CLIENT_ID_PREFIX}-{client_type}",
        "security.protocol": settings.KAFKA_SECURITY_PROTOCOL.upper(),
        "request.timeout.ms": settings.KAFKA_REQUEST_TIMEOUT_MS,
        "metadata.max.age.ms": settings.KAFKA_METADATA_MAX_AGE_MS,
    }

    if "SASL" in settings.KAFKA_SECURITY_PROTOCOL.upper():
        config.update({
            "sasl.mechanism": settings.KAFKA_SASL_MECHANISM,
            "sasl.username": settings.KAFKA_SASL_USERNAME,
            "sasl.password": settings.KAFKA_SASL_PASSWORD,
        })

    return config