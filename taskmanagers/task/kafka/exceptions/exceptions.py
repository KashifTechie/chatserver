# ==============================================================================
# Domain-Specific Exceptions for Kafka Integration
# Provides clean errors representing various lifecycle failure states.
# ==============================================================================

class KafkaIntegrationError(Exception):
    """Base exception class for all Kafka integration errors."""
    pass


class SerializationError(KafkaIntegrationError):
    """Raised when an outgoing event object fails to serialize into JSON/bytes."""
    pass


class DeserializationError(KafkaIntegrationError):
    """Raised when an incoming Kafka record fails to parse or decode."""
    pass


class ProcessingError(KafkaIntegrationError):
    """Raised when a business event handler fails to process a valid message."""
    pass


class TransientProcessingError(ProcessingError):
    """
    Indicates a temporary business processing failure (e.g., database lock, 
    external API timeout). The consumer should attempt a retry.
    """
    pass


class PermanentProcessingError(ProcessingError):
    """
    Indicates a non-recoverable processing error (e.g., business constraint validation 
    violation, missing required attributes). 
    The event should bypass retries and go straight to the Dead Letter Queue.
    """
    pass
