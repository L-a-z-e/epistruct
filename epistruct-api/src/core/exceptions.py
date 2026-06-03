import uuid

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str, detail: str = ""):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.detail = detail


class NotFoundError(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(status.HTTP_404_NOT_FOUND, code, message)


class ForbiddenError(AppError):
    def __init__(self, code: str = "AUTH_FORBIDDEN", message: str = "Access denied"):
        super().__init__(status.HTTP_403_FORBIDDEN, code, message)


class UnauthorizedError(AppError):
    def __init__(self, code: str = "AUTH_UNAUTHORIZED", message: str = "Authentication required"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, code, message)


class ConflictError(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(status.HTTP_409_CONFLICT, code, message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": exc.status_code,
                "code": exc.code,
                "message": exc.message,
                "detail": exc.detail,
                "instance": str(request.url),
                "trace_id": str(uuid.uuid4()),
            },
        )
