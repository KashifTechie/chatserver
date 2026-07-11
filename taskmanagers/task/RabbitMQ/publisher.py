import json
from taskmanagers.task.RabbitMQ.connection import get_connection
from pika import BasicProperties
from taskmanagers.task.RabbitMQ.config import RABBITMQ_SERVER_TOPOLOGY
import logging

logger  = logging.getLogger(__name__)

class RMQProducer:

    def __init__(self):
        self.connection, self.channel = get_connection()

        # enable publisher confirms
        self.channel.confirm_delivery()

    def producer(self,exchange, routing_key, payload):
        try:
            self.channel.basic_publish(
                        exchange=exchange,
                        routing_key=routing_key,
                        body=json.dumps(payload),
                        properties= BasicProperties(
                        delivery_mode=2,
                        content_type="application/json",
                        ),
                        mandatory=True,
                    )
            logger.info("The message %s has been published to RabbitMQ", payload.get("task"))
        
            
        except Exception as e:
            raise RuntimeError(f"publish failed: {e}")

    def close(self):
        self.connection.close() 

    def execute_task(self, task, *args, **kwargs):
        
        event = kwargs.pop("event")

        route = RABBITMQ_SERVER_TOPOLOGY["routes"][event]
        exchange = RABBITMQ_SERVER_TOPOLOGY["exchanges"][route["exchange"]]
        exchange_name = exchange["name"]
        routing_key = route["routing_key"]
        payload = {
            "task": task.__name__,
            "args": args,
            "kwargs": kwargs
        }    

        self.producer(exchange_name, routing_key, payload)

