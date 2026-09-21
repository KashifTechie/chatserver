from typing import Type
from multiprocessing.sharedctypes import Value
import json
import logging
from taskmanagers.task.kafka.exceptions.exceptions import PermanentProcessingError


logger = logging.getLogger(__name__)


class EventSerializer:

    REQUIRED_FIELDS = {'event_id', 'event_type', 'version', 'timestamp', 'data'}

    def serialize(self, envelope: dict) -> bytes:
        """
        Validates event envelope structure and serializes it to JSON bytes.
        """

        if not isinstance(envelope, dict):
            raise ValueError("Event envelope must be a dictionary")

        missing = self.REQUIRED_FIELDS - set(envelope.keys())

        if missing:
            raise ValueError(f"Envelope is missing the required fields: {missing}")
        
        try:
            json_str = json.dumps(envelope)
            return json_str.encode("utf-8")
        except (TypeError, ValueError) as err:
            raise  ValueError(f"Failed to serialize event envelope to JSON: {err}")

class EventDeserializer:
    """
    Handles deserialization and basic decoding of incoming messages.
    """
    def deserializer(self, raw_bytes):
        """
        Decodes raw bytes to UTF-8 and parses them to a dictionary.
        Raises PermanentProcessingError if the message is malformed, invalid JSON, or cannot be parsed.
        """
        if raw_bytes is None:
            return {}
        
        try:

            # 1. Decode bytes to string
            try:
                val_str = raw_bytes.decode("utf-8")
            except UnicodeDecodeError as err:
                raise PermanentProcessingError(f"Failed to decode message bytes as UTF-8 string: {err}")

            # 2. Parse JSON
            try:
                payload = json.loads(val_str)
                return payload
            except json.JSONDecodeError as err:
                raise PermanentProcessingError(f"Failed to parse event JSON payload: {err}")

        except PermanentProcessingError:
            raise
        except Exception as err:
            raise PermanentProcessingError(f"Failed to deserialize raw message: {err}")

