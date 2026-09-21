# from kafka.admin import new_topic
# from kafka.admin import new_topic
from confluent_kafka import version
from confluent_kafka import Producer, KafkaException
from taskmanagers.task.kafka.config.producer import get_producer_config
import logging
from functools import lru_cache
import uuid
from datetime import datetime, timezone
from taskmanagers.task.kafka.serializers.serializer import EventSerializer
from django.conf import settings
from prometheus_client import Counter
import signal


logger = logging.getLogger(__name__)

class KafkaProducer:

    KAFKA_MESSAGES_TOTAL = Counter(
        "kafka_producer_messages_total",
        "Total Kafka messages processed by producer",
        ["topic", "status"],
    )

    KAFKA_DELIVERY_FAILURE_TOTAL = Counter(
        "kafka_producer_delivery_failures_total",
        "Total Kafka delivery failures",
        ["topic"],
    )

    VERSION = settings.TASK_MANAGER_VERSION

    def __init__(self):
        self.config = get_producer_config()
        self._producer = Producer(self.config)
        signal.signal(
            signal.SIGTERM,
            self._graceful_shutdown,
        )

        signal.signal(
            signal.SIGINT,
            self._graceful_shutdown,
        )

    def _delivery_callback(self, err, msg):
        """
        Triggered when a message is successfully written to the broker or fails.
        Runs on the thread calling poll() or flush().
        """
        topic = msg.topic()
        if err is not None:
            logger.error(f"[Producer] Message delivery failed: {err}")

            self.KAFKA_MESSAGES_TOTAL.labels(
                topic=topic,
                status="failed",
            ).inc()

            self.KAFKA_DELIVERY_FAILURE_TOTAL.labels(
                topic=topic,
            ).inc()

        else:
            raw_key = msg.key()
            if raw_key is not None:
                try:
                    key = raw_key.decode("utf-8")
                except UnicodeDecodeError:
                    key = repr(raw_key)
            else:
                key=None

            self.KAFKA_MESSAGES_TOTAL.labels(
                topic=topic,
                status="success",
            ).inc()

            logger.info(
                f"[Producer] Message delivered successfully to '{msg.topic()}' "
                f"Partition [{msg.partition()}] at Offset {msg.offset()} (Key: {key})"
            )

    def publish(self, topic:str, value:str|bytes, key:str|bytes=None, headers:list=None) -> None:
        """
        Publishes a raw payload value, key, and optional headers to Kafka asynchronously.
        
        :param topic: The target topic name.
        :param value: Raw message payload (string or bytes).
        :param key: Optional routing key (string or bytes).
        :param headers: Optional list of tuples (e.g. [('header_key', b'header_val')]).
        """

        value_bytes = value.encode("utf-8") if isinstance(value, str) else value
        key_bytes = key.encode("utf-8") if isinstance(key, str) else key

        logger.info("[Producer] is queuing the message with key: %s to topic : %s", key, topic)

        try:
            self._producer.produce(
                topic=topic,
                key=key_bytes,
                value=value_bytes,
                headers=headers,
                callback=self._delivery_callback
            )
            self._producer.poll(0)
            logger.info("[producer] has successfully been enqueued")
        except BufferError:
            logger.info("[Producer] local buffer is full, Triggeriing poll to make some space...")
            self._producer.poll(0.5)

            try:
                self._producer(
                    topic=topic,
                    key=key_bytes,
                    value=value,
                    headers=headers,
                    callback=self._delivery_callback()
                )
                self._producer.poll(0)
                logger.info("[Producer] Retried message successfully enqueued after polling.")
            except BufferError as BE:
                logger.error("[Producer] Buffer full error persisted after retry. Raising exception to application layer.")
                raise BE
        except KafkaException:
            logger.exception("[Producer] Kafka publishing failed.")
            raise

    def execute_task(self, task, *args, **kwargs):
        try:
            logger.warning("[TaskHandler] execute_task invoked. Mapping to compatibility structured event envelope.")

            task = f"task.{task.__name__}"
            topic = f"task.{task.__name__}"
            event_id = f"evt_{uuid.uuid4()}"
            event_type = f"task_{task}"
            timestamp = datetime.now(timezone.utc).isoformat()
            # pyrefly: ignore [missing-import]
            
            data = {
                "task":task,
                "args":list(args),
                "kwargs": kwargs
            }

            event_envelope = {
                "event_id":event_id,
                "event_type":event_type,
                "version":self.VERSION,
                "timestamp":timestamp,
                "data":data,
            }

            event_serialized =( 
                EventSerializer()
                .serialize(event_envelope)
            )

            self.publish(
                topic=topic,
                value=event_serialized,
                key=event_id,
                headers=None,
            )

            logger.info(f"[TaskHandler] Dispatching event '{event_type}' (ID: {event_envelope['event_id']}) to topic '{topic}'")

        except Exception as e:
            logger.exception(
                "[production]: an error occured while dispatching the message: %s", 
                str(e)
            )
            raise

    def flush(self, timeout: float=5.0) -> int:
        """
        Blocks until all pending messages in the producer queue are delivered.
        Returns the number of messages remaining undelivered.
        """
        logger.info("[producer] flushing the outstanding messages...")
        return self._producer.flush(timeout)

    def close(self):
        """
        Flushes and releases resources. Call this on application shutdown.
        """
        remaining = self.flush(timeout=10.0)
        if remaining > 0:
            logger.info("[producer] shutting down: %s messages remained undelivered \nafter flush out") 

        else:
            logger.info("[Producer] Producer shutdown completed successfully.")


    def _graceful_shutdown(self, signum, frame):
        logger.info(
            "[Producer] Shutdown signal received: %s",
            signum,
        )

        self.close()

@lru_cache
def get_producer() -> KafkaProducer:
    """
    Returns a global process-level long-lived KafkaProducer instance.
    Prevents creating redundant TCP connection overhead on every publish action.
    """
    return KafkaProducer()

