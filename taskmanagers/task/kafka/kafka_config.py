from django.conf import settings

KAFKA_CONFIG = settings.KAFKA_BOOTSTRAP_SERVERS

def get_consumer_config(group_id: str) -> dict:
    """Generate consumer config for specific group"""
    return {
        'bootstrap.servers': KAFKA_CONFIG,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
        'max.poll.interval.ms': 300000,
        'session.timeout.ms': 10000,
        'heartbeat.interval.ms': 3000,
    }

def get_producer_config() -> dict:
    return {
    'bootstrap.servers': KAFKA_CONFIG,
    'client.id': 'django-producer',
    'acks': 'all',
    'retries': 3,
    'compression.type': 'lz4',
    'enable.idempotence': True,
}
    
