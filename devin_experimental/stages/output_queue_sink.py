"""Output queue sink stage for collecting pipeline results."""

import queue
from typing import Any, List, Optional

import ray
from pydantic import BaseModel, Field

from nv_ingest.framework.orchestration.ray.stages.meta.ray_actor_sink_stage_base import RayActorSinkStage


class OutputQueueSinkConfig(BaseModel):
    """Configuration for OutputQueueSinkStage."""

    max_buffer_size: int = Field(default=1024, ge=1)


@ray.remote
class OutputQueueSinkStage(RayActorSinkStage):
    """
    A sink stage that collects results into an in-memory queue.

    Results can be retrieved via get_next() or get_many() method calls.
    """

    def __init__(self, config: OutputQueueSinkConfig, stage_name: Optional[str] = None) -> None:
        super().__init__(config, log_to_stdout=False, stage_name=stage_name)
        self.config: OutputQueueSinkConfig
        self._buffer: "queue.Queue[Any]" = queue.Queue(maxsize=self.config.max_buffer_size)

    def on_data(self, control_message: Any):
        """Called when data arrives at this sink."""
        try:
            self._buffer.put_nowait(control_message)
        except queue.Full:
            self.stats["queue_full"] += 1

    @ray.method(num_returns=1)
    def get_next(self, timeout_s: Optional[float] = None) -> Optional[Any]:
        """Get the next result, blocking up to timeout_s seconds."""
        try:
            return self._buffer.get(timeout=timeout_s)
        except queue.Empty:
            return None

    @ray.method(num_returns=1)
    def get_many(self, max_items: int, timeout_s: Optional[float] = None) -> List[Any]:
        """Get up to max_items results, blocking for the first one."""
        items = []

        if max_items <= 0:
            return items

        first = None
        try:
            first = self._buffer.get(timeout=timeout_s)
        except queue.Empty:
            return items

        items.append(first)

        while len(items) < max_items:
            try:
                items.append(self._buffer.get_nowait())
            except queue.Empty:
                break

        return items

    @ray.method(num_returns=1)
    def size(self) -> int:
        """Return the current number of items in the queue."""
        return self._buffer.qsize()
