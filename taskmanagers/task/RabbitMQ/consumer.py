import json
from chat.tasks import process_message
from taskmanagers.task.RabbitMQ.connection import get_connection, BlockingConnection
from taskmanagers.task.RabbitMQ.config import RABBITMQ_SERVER_TOPOLOGY
import logging

logger = logging.getLogger(__name__)

class RMQConsumer:

    def __init__(self, queue):
        self.conn, self.channel = get_connection()
        self.channel.basic_qos(prefetch_count=10)
        self.queue = queue

        self.queue_config = RABBITMQ_SERVER_TOPOLOGY.get("queues")

        self.HANDLER_GROUPS_MAP = {
            self.queue_config.get("message").get("name") : {
                "process_message" : process_message
            }
        }

    def run_consumer(self):

        logger.info("The rmq consumer has started")

        handlers = self.HANDLER_GROUPS_MAP.get(self.queue)

            
        def callback(ch, method, properties, body):
            logger.info("The callback recieved for from the queue %s",self.queue)
            payload = json.loads(body)
            task = payload.get("task")
            args = payload.get("args", [])
            kwargs = payload.get("kwargs", {})
            logger.info("The handler %s is being called", task)
            try:
                logger.info("The function is callable : %s", callable(handlers[task]))
                handlers[task](*args, **kwargs)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception:
                ch.basic_nack(
                    delivery_tag=method.delivery_tag,
                    requeue=False
                )

        self.channel.basic_consume(
            queue=self.queue,
            on_message_callback=callback
        )

        self.channel.start_consuming()

    def close(self):
        self.channel.close()