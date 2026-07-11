from .kafka_config import get_consumer_config
from .task_map import CONSUMER_GROUP_MAPPINGS
from confluent_kafka import Consumer, KafkaError, KafkaException
from django_redis import get_redis_connection
import logging
import threading
import json

logger = logging.getLogger(__name__)

PRIORITY_MAP = {
    "high": 0,
    "medium": 1,
    "low": 2,
}

class KafkaConsumer:

    def __init__(self, group_name: str, topics=None, worker_count=4):
        self.group_name = group_name
        config = get_consumer_config(group_name)
        self.consumer = Consumer(config)
        self.running = True
        self.worker_count = worker_count
        self.redis = get_redis_connection("default")

        group_tasks = CONSUMER_GROUP_MAPPINGS.get(group_name, None)
        if not group_tasks:
            raise ValueError(f"No task mappings found for group: {group_name}")
        
        if topics:
            self.task_mapping = {t : group_tasks[t] for t in topics if t in group_tasks}
        else:
            self.task_mapping = group_tasks

        logger.info(f"KafkaConsumer initialized for group: {group_name} with topics: {list(self.task_mapping.keys())}")

    def shut_down(self):
        self.running = False
        self.consumer.close()

    def start_consuming(self):

        if not self.task_mapping:
            logger.error("No topics to subscribe to. Exiting consumer.")
            raise ValueError("No topics to subscribe to.")
        topics_subscribe = list(self.task_mapping.keys())
        try:
            self.consumer.subscribe(topics_subscribe)
            logger.info(f"Subscribed to topics: {topics_subscribe}")
        except KafkaException as e:
            logger.error(f"Failed to subscribe to topics: {str(e)}")
            raise str(e)
        
        for i in range(self.worker_count):
            threading.Thread(target=self.worker, args=(i,), daemon=True).start()
            logger.info(f"Started consumer worker thread {i+1}/{self.worker_count}")

        try:
            self.start()
        except Exception as e:
            logger.error(f"Error starting consumer workers: {str(e)}")
            raise str(e)    

    def worker(self, worker_id: int):
        logger.info(f"Worker {worker_id} started.")
        while self.running:
            try:
                data = self.redis.zpopmin(f"priority_queue_{self.group_name}", 1)
                if not data:
                    continue
                payload = json.loads(data[0][0])
                task_name = payload.get("task")
                args = payload.get("args", [])
                kwargs = payload.get("kwargs", {})

                # task_name = payload.get

                if task_name in self.task_mapping:

                    self.task_mapping[task_name](*args, **kwargs)
                else:
                    logger.warning(f"Worker {worker_id}: No task found for {task_name}")
                    continue
            except Exception as e:
                logger.error(f"Worker {worker_id} encountered error: {str(e)}")     


    def start(self):
        

        try:
            while self.running:
                msg = self.consumer.poll(1.0)
                if not msg:
                    continue
                elif msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"End of partition reached {msg.topic()} [{msg.partition()}]")
                        raise KafkaException(msg.error())
                else:
                    header = dict(msg.headers() or [])
                    prioriy = header.get("priority", b"medium").decode()  
                    prio = PRIORITY_MAP.get(prioriy,2)

                    data = msg.value().decode("utf-8")

                    self.redis.zadd(f"priority_queue_{self.group_name}", {data: prio})

                    self.consumer.commit(msg)

        except Exception as e:
            logger.error(f"Error starting consumer workers: {str(e)}")
            raise str(e)

