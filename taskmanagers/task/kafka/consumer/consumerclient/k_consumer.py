import threading
import logging


logger = logging.getLoger(__name__)

class TreadSafeOffsetTracker:
    def __init__(self):
        self.thread_lock = threading.Lock()
        self._inflight = {}
        self._last_safe_offset = {}

    def register(self, topic: str, partition: str, offset: int):
        """
        Register a message with its offset.
        """
        with self.thread_lock:
            key = (topic, partition)
            if key not in self._inflight:
                self._inflight[key] = {}
            self._inflight[key][offset] = False
        
    
    def complete(self, topic: str, partition: str, offset: int):
        """
        Marks offset completed. Returns the next contiguous offset to commit, or None.
        """

        with self.thread_lock:
            key = (topic, partition)
            if key not in self._inflight or offset not in self._inflight[key]:
                return None
        
            # Mark this specific offset as done
            self._inflight[key][offset] = True

            # Find the first consecutive unprocessed offset starting from the last safe offset
            sorted_offsets = sorted(self._inflight[key].keys())
            commit_offset = None
            
            for off in sorted_offsets:
                if self._inflight[key][off]:
                    commit_offset = off
                    del self._inflight[key][off]
                else:
                    break
        
            if commit_offset is not None:
                next_offset = commit_offset + 1
                self._last_safe_offser[key] = next_offset
                return next_offset
            return None

    def get_committable_offsets(self)-> dict:
        """Returns the last known-safe offset per partition, for use at shutdown."""
        with self.thread_lock:
            # Return a snapshot, not the live dict
            return dict(self._last_safe_offset)
    
    def get_inflight_count(self)-> int:
        """Returns the number of messages currently being processed."""
        with self.thread_lock:
            return sum(len(inflight) for inflight in self._inflight.values())
    
    def clear_partition(self, topic: str, partition: int) -> None:
        with self.thread_lock:
            key = (topic, partition)
            if key in self._inflight:
                logger.info(f"[Tracker] Clearing in-flight tracking for partition {topic}:{partition} due to revocation.")
                del self._inflight[key]
