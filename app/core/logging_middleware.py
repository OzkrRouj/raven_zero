import time
import uuid

import structlog
from fastapi import Request

from app.core.logger import logger


async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    start_time = time.time()

    try:
        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            "request_finished",
            status_code=response.status_code,
            duration=f"{process_time:.4f}s",
        )

        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.exception(
            "request_failed", error=str(e), duration=f"{process_time:.4f}s"
        )
        raise
