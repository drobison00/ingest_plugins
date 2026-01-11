"""Direct submit source stage for in-process job submission."""

import queue
import threading
import time
from typing import Any, Optional

import ray
from pydantic import BaseModel, Field

from nv_ingest.framework.orchestration.ray.stages.meta.ray_actor_source_stage_base import RayActorSourceStage


class DirectSubmitSourceConfig(BaseModel):
    """Configuration for DirectSubmitSourceStage."""

    poll_interval: float = Field(default=0.05, gt=0)
    max_buffer_size: int = Field(default=1024, ge=1)


@ray.remote
class DirectSubmitSourceStage(RayActorSourceStage):
    """
    A source stage that accepts control messages directly via method calls.

    This stage allows in-process submission of work to the pipeline without
    going through a message broker.
    """

    def __init__(self, config: DirectSubmitSourceConfig, stage_name: Optional[str] = None) -> None:
        super().__init__(config, log_to_stdout=False, stage_name=stage_name)
        self.config: DirectSubmitSourceConfig
        self._buffer: "queue.Queue[Any]" = queue.Queue(maxsize=self.config.max_buffer_size)
        self._pause_event = threading.Event()
        self._pause_event.set()
        self.output_queue = None

    @ray.method(num_returns=1)
    def submit(self, control_message: Any, block: bool = True, timeout_s: Optional[float] = None) -> bool:
        """Submit a single control message."""
        try:
            self._buffer.put(control_message, block=block, timeout=timeout_s)
            return True
        except queue.Full:
            return False

    @ray.method(num_returns=1)
    def submit_many(self, control_messages: Any, block: bool = True, timeout_s: Optional[float] = None) -> int:
        """Submit a batch of control messages. Returns the number accepted."""
        accepted = 0
        try:
            for cm in control_messages:
                try:
                    self._buffer.put(cm, block=block, timeout=timeout_s)
                    accepted += 1
                except queue.Full:
                    break
        except Exception:
            return accepted
        return accepted

    def _read_input(self) -> Optional[Any]:
        if not self._running:
            return None
        try:
            return self._buffer.get(block=True, timeout=self.config.poll_interval)
        except queue.Empty:
            return None

    def _processing_loop(self) -> None:
        while self._running:
            try:
                control_message = self._read_input()
                if control_message is None:
                    continue

                self._active_processing = True

                if self.output_queue is None:
                    time.sleep(self.config.poll_interval)
                    continue

                if not self._pause_event.is_set():
                    self._active_processing = False
                    self._pause_event.wait()
                    self._active_processing = True

                object_ref_to_put = None
                try:
                    owner_actor = self.output_queue.actor
                    object_ref_to_put = ray.put(control_message, _owner=owner_actor)
                    del control_message

                    is_put_successful = False
                    while not is_put_successful and self._running:
                        try:
                            self.output_queue.put(object_ref_to_put)
                            self.stats["successful_queue_writes"] += 1
                            is_put_successful = True
                        except Exception:
                            self.stats["queue_full"] += 1
                            time.sleep(0.1)

                    self.stats["processed"] += 1

                finally:
                    if object_ref_to_put is not None:
                        del object_ref_to_put

            except Exception:
                self.stats["errors"] += 1
                time.sleep(self.config.poll_interval)
            finally:
                self._active_processing = False
                self._shutdown_signal_complete = True

    @ray.method(num_returns=1)
    def start(self) -> bool:
        """Start the processing loop."""
        if self._running:
            return False
        self._running = True
        threading.Thread(target=self._processing_loop, daemon=True).start()
        return True

    @ray.method(num_returns=1)
    def stop(self) -> bool:
        """Stop the processing loop."""
        self._running = False
        return True

    @ray.method(num_returns=1)
    def set_output_queue(self, queue_handle: Any) -> bool:
        """Set the output queue for this stage."""
        self.output_queue = queue_handle
        return True

    @ray.method(num_returns=1)
    def pause(self) -> bool:
        """Pause processing."""
        self._pause_event.clear()
        return True

    @ray.method(num_returns=1)
    def resume(self) -> bool:
        """Resume processing."""
        self._pause_event.set()
        return True
