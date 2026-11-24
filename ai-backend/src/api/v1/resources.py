"""Resource Management & Telemetry API router — thin HTTP/SSE controller."""

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from src.core.security import get_current_user, get_current_user_or_query
from src.core.telemetry import metric_logger, quota_manager, sse_manager
from src.models.v1.resource import UserQuotaEntity
from src.schemas.v1.resources import ResourceHistoryData

resources_router = APIRouter(prefix="/resources", tags=["Resource Management & Telemetry"])


@resources_router.get("/summary")
async def get_resources_summary(
    range: str = Query("24h", pattern="^(1h|24h|7d|30d)$", description="Khung thời gian lọc thống kê"),
    current_user: dict = Depends(get_current_user),
):
    """OP-018: KPI Summary & Quota status (strictly owner-scoped, BR-021)."""
    summary = await asyncio.to_thread(metric_logger.get_metrics_summary, current_user["id"], range)
    return {"status": "success", "data": summary}


@resources_router.get("/quota")
async def get_user_quota_info(current_user: dict = Depends(get_current_user)):
    """OP-020: Daily token quota status for the authenticated user."""
    user_id = current_user["id"]
    quota = await asyncio.to_thread(quota_manager.get_or_create_quota, user_id)
    return {"status": "success", "data": UserQuotaEntity.from_quota_row(user_id, quota).to_status_dict()}


@resources_router.get("/history")
async def get_resources_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """OP-021: Paginated API telemetry history for the authenticated user."""
    history = await asyncio.to_thread(metric_logger.get_metrics_history, current_user["id"], limit, offset)
    data = ResourceHistoryData(items=history, count=len(history), limit=limit, offset=offset)
    return {"status": "success", "data": data.model_dump()}


@resources_router.get("/stream")
async def stream_resource_telemetry(current_user: dict = Depends(get_current_user_or_query)):
    """OP-019: Real-time Server-Sent Events (SSE) telemetry & quota stream (NFR-021)."""
    user_id = current_user["id"]
    queue = await sse_manager.connect(user_id)

    async def sse_generator():
        try:
            summary = await asyncio.to_thread(metric_logger.get_metrics_summary, user_id, "24h")
            yield f"event: initial_state\ndata: {json.dumps(summary, ensure_ascii=False)}\n\n"

            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield payload
                except asyncio.TimeoutError:
                    ts = datetime.now(timezone.utc).isoformat()
                    yield f"event: ping\ndata: {json.dumps({'timestamp': ts})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await sse_manager.disconnect(user_id, queue)

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
