import time
from uuid import uuid4

from fastapi import Request


async def build_request_context(request: Request) -> dict[str, str | float]:
    started_at = time.perf_counter()
    request_id = request.headers.get("x-request-id", str(uuid4()))
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    return {"request_id": request_id, "elapsed_ms": round(elapsed_ms, 2)}
