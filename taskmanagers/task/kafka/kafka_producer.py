
from confluent_kafka import Producer, KafkaError
from django.conf import settings
import json 
from taskmanagers.task.kafka.kafka_config import get_producer_config
import logging

logger = logging.getLogger(__name__)

PRODUCER_CONFIG = get_producer_config()

class KafkaProducer:
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._producer = Producer(PRODUCER_CONFIG)

        return cls._instance

    def set_priority(self, priority):
        pass

    def delivery_report(self, err, msg):
        if err is not None:
            logger.info(f"Message delivery failed: {err}")
        else:
            logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")
    
    def produce(self,data, key):
        try:

            topic = data.get("task")
            # value = data.get("value")
            message = json.dumps(data).encode('utf-8')
            self._producer.produce(
                topic=topic,
                value=message,
                key=key,
                callback=self.delivery_report,
                # header=self.set_priority()
                headers=[("priority", b"high")]
            )
            self._producer.poll(0)
            logger.info(f"The task has been sent to kafka server via topic : {topic}")
        except KafkaError as e:
            print(f"Failed to produce message: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def execute_task(self, task, *args, **kwargs):

        message = {
            "task": task.__name__,
            "args": args,
            "kwargs": kwargs
        }    

        self.produce(message, key=str(kwargs.get("id", "")))