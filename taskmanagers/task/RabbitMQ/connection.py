from pika import ConnectionParameters, BlockingConnection, PlainCredentials
from django.conf import settings

def get_connection():
    
    credentials = PlainCredentials(
        settings.RMQ_USERNAME,
        settings.RMQ_PASSWORD,
    )

    parameters = ConnectionParameters(
            host=settings.RMQ_HOST,
            port= settings.RMQ_PORT,
            credentials=credentials,
            heartbeat=60,
            blocked_connection_timeout=30
    )   
    
    connection = BlockingConnection(parameters)

    channel = connection.channel()

    return connection, channel