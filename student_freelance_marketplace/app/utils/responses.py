"""
utils/responses.py
───────────────────
Standardised API response helpers so every endpoint returns
a consistent JSON envelope.
"""

from typing import Any, Optional
from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data,
        },
    )


def error_response(
    message: str,
    status_code: int = 400,
    details: Optional[Any] = None,
) -> JSONResponse:
    body: dict = {"success": False, "message": message}
    if details:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body)


def paginated_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
    message: str = "Success",
) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": message,
            "data": {
                "items": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": -(-total // page_size),  # ceiling division
                },
            },
        },
    )
