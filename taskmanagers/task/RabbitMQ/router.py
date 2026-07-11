from .connection import get_connection
from pika import BlockingConnection
from .config import RABBITMQ_SERVER_TOPOLOGY
import logging
logger = logging.getLogger(__name__)


def setup_topology():
    connection, channel = get_connection()
    
    try:
        for exchange in RABBITMQ_SERVER_TOPOLOGY["exchanges"].values():
            channel.exchange_declare(
                exchange=exchange.get("name"),
                exchange_type=exchange.get("type"),
                durable=True
            )
        
        for queue in RABBITMQ_SERVER_TOPOLOGY["queues"].values():
            queue_name = queue.get("name")

            if not queue_name:
                raise ValueError(f"Queue name missing in config {queue}")

            channel.queue_declare(
                queue=queue_name,
                durable=True
            )

        for route in RABBITMQ_SERVER_TOPOLOGY["routes"].values():

            exchange = RABBITMQ_SERVER_TOPOLOGY["exchanges"][route["exchange"]]
            queue = RABBITMQ_SERVER_TOPOLOGY["queues"][route["queue"]]
            routing_key = route["routing_key"]
            channel.queue_bind(
                exchange=exchange["name"],
                queue=queue["name"],
                routing_key=routing_key
            )

            logger.info(f"Binding queue {queue["name"]} -> exchange {exchange["name"]} with key {routing_key}")

            
    except Exception as e:
        logger.exception("Failed to setup RabbitMQ topology: %s", e)
        raise Exception(str(e))
    finally:
        try:
            channel.close()
        except Exception:
            pass
        connection.close()


