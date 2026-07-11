from django.core.management import BaseCommand
from taskmanagers.task.RabbitMQ.consumer import RMQConsumer
from taskmanagers.task.RabbitMQ.router import setup_topology
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument(
            "--queue",
            type=str,
            help="consumer queue name"
        )

    def handle(self, *args, **kwargs):

        logger.info("The commmand is starting to run consumer")
        queue = kwargs.get("queue")
        try:
            setup_topology()
            
            rmq_consumer = RMQConsumer(queue)

            rmq_consumer.run_consumer()

        except KeyboardInterrupt:
            logger.info("Kafka consumer stopped by user (Ctrl+C).")
        except Exception as e:
            logger.exception("Error while running Kafka consumer: %s", e)
        finally:
            rmq_consumer.close()