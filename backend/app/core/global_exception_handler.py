from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from datetime import datetime
import uuid

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "data": None,
            "error": {
                "message": exc.detail
            },
            "meta": {
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "data": None,
            "error": {
                "message": "Internal server error"
            }
        }
    )