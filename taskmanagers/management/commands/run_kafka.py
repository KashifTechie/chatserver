from django.core.management import BaseCommand
from taskmanagers.task.kafka.kafka_consumer import KafkaConsumer
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def add_arguments(self, parser):

        parser.add_argument(
            "--group",
            type=str,
            help="consumer queue name"
        )

    def handle(self, *args, **kwargs):

        logger.info("The commmand is starting to run consumer")
        group = kwargs.get("group")
        try:
            kafka_consumer = KafkaConsumer(
                                group_name=group
                            )
                            

            kafka_consumer.start_consuming()

        except KeyboardInterrupt:
            logger.info("Kafka consumer stopped by user (Ctrl+C).")
        except Exception as e:
            logger.exception("Error while running Kafka consumer: %s", e)
        finally:
            kafka_consumer.shut_down()