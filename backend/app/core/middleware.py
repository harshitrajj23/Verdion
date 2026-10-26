import json
import time
import uuid
from typing import Callable, Dict
from fastapi import Request, Response
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# In-memory idempotency cache (or DB-backed)
IDEMPOTENCY_CACHE: Dict[str, Dict] = {}


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates X-Trace-ID on every incoming request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = request.headers.get("X-Trace-ID") or f"trace_{uuid.uuid4().hex[:12]}"
        request.state.trace_id = trace_id

        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Guarantees idempotency on state-changing requests using Idempotency-Key header.
    PRD Section 15.1: "Use idempotency keys for transaction-producing operations."
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        idempotency_key = None
        if request.method in ["POST", "PATCH"]:
            idempotency_key = request.headers.get("Idempotency-Key")
            if idempotency_key:
                # Check cache
                cached = IDEMPOTENCY_CACHE.get(idempotency_key)
                if cached:
                    # Return cached response directly
                    return JSONResponse(
                        status_code=cached["status_code"],
                        content=cached["content"],
                        headers={**cached.get("headers", {}), "X-Idempotent-Replay": "true"}
                    )

        response = await call_next(request)

        if idempotency_key and response.status_code < 400:
            # Capture and cache response body for subsequent playback
            try:
                response_body = [chunk async for chunk in response.body_iterator]
                response.body_iterator = iterate_in_threadpool(iter(response_body))
                body_bytes = b"".join(response_body)
                parsed_json = json.loads(body_bytes.decode("utf-8"))
                IDEMPOTENCY_CACHE[idempotency_key] = {
                    "status_code": response.status_code,
                    "content": parsed_json,
                    "headers": {"content-type": "application/json"}
                }
            except Exception:
                pass

        return response
