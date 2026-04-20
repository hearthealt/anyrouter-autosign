"""
SSE 事件流 API
"""
import asyncio
import json
import queue
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user_with_query_token
from app.models import User
from app.services.events import event_bus

router = APIRouter(tags=["事件"])


def encode_sse(data: dict, event: str | None = None, event_id: str | None = None) -> str:
    """将事件编码为 SSE 格式。"""
    lines = []
    if event_id:
        lines.append(f"id: {event_id}")
    if event:
        lines.append(f"event: {event}")
    payload = json.dumps(data, ensure_ascii=False)
    lines.append(f"data: {payload}")
    return "\n".join(lines) + "\n\n"


@router.get("/events")
async def stream_events(
    request: Request,
    current_user: User = Depends(get_current_user_with_query_token),
):
    """建立 SSE 事件流连接。"""
    subscriber_id, event_queue = event_bus.subscribe()

    async def event_generator():
        try:
            yield encode_sse(
                {
                    "user_id": current_user.id,
                    "username": current_user.username,
                    "connected_at": datetime.now().isoformat(),
                },
                event="connected",
                event_id=f"connected-{subscriber_id}",
            )

            while True:
                if await request.is_disconnected():
                    break

                try:
                    event = await asyncio.to_thread(event_queue.get, True, 15)
                    yield encode_sse(event, event=event.get("type"), event_id=event.get("id"))
                except queue.Empty:
                    yield encode_sse(
                        {"timestamp": datetime.now().isoformat()},
                        event="ping",
                    )
        finally:
            event_bus.unsubscribe(subscriber_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
