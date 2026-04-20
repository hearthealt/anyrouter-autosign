"""
SSE 事件总线
"""
from __future__ import annotations

import queue
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, Tuple


class EventBus:
    """线程安全的进程内事件总线。"""

    def __init__(self):
        self._lock = threading.Lock()
        self._subscribers: Dict[str, queue.Queue] = {}

    def subscribe(self) -> Tuple[str, queue.Queue]:
        subscriber_id = uuid.uuid4().hex
        event_queue: queue.Queue = queue.Queue(maxsize=200)
        with self._lock:
            self._subscribers[subscriber_id] = event_queue
        return subscriber_id, event_queue

    def unsubscribe(self, subscriber_id: str) -> None:
        with self._lock:
            self._subscribers.pop(subscriber_id, None)

    def publish(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = {
            "id": uuid.uuid4().hex,
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            **payload,
        }

        with self._lock:
            subscribers = list(self._subscribers.values())

        for subscriber in subscribers:
            try:
                subscriber.put_nowait(event)
            except queue.Full:
                try:
                    subscriber.get_nowait()
                except queue.Empty:
                    pass
                try:
                    subscriber.put_nowait(event)
                except queue.Full:
                    pass

        return event


event_bus = EventBus()


def publish_event(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """发布服务端事件。"""
    return event_bus.publish(event_type, payload)
