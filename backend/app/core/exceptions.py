import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger("app")


class AppError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, resource: str = "Record"):
        super().__init__(f"{resource} not found.", status.HTTP_404_NOT_FOUND)


class ValidationAppError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class ConflictError(AppError):
    def __init__(self, message: str = "This action conflicts with existing data."):
        super().__init__(message, status.HTTP_409_CONFLICT)


class AuthError(AppError):
    def __init__(self, message: str = "Invalid credentials."):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class PermissionDeniedError(AppError):
    def __init__(self, message: str = "You do not have permission to do this."):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class RateLimitError(AppError):
    def __init__(self, message: str = "Too many requests. Please slow down."):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)


def _error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        first = errors[0] if errors else None
        if not first:
            return _error_response("Please check your input.", status.HTTP_422_UNPROCESSABLE_ENTITY)
        field = ".".join(str(p) for p in first["loc"] if p != "body")
        if first["type"] == "missing":
            message = f"'{field}' is required." if field else "A required field is missing."
        else:
            # Pydantic prefixes a field_validator's own `raise
            # ValueError(...)` with "Value error, " -- stripping that lets
            # this app's own specific, hand-written validator messages
            # (e.g. app/schemas/client.py's _phone_validator: "mobile must
            # be a valid phone number (at least 7 digits)",
            # _kuwait_mobile_validator, the expiry-after-issue-date checks)
            # reach the user exactly as written, instead of every one of
            # them being discarded in favor of a generic "Please check the
            # '{field}' field." that never said what was actually wrong --
            # the same silent-message-loss bug httpClient.ts's
            # extractErrorMessage() comment already documents for AppError,
            # just one layer deeper, for Pydantic's own validation errors.
            raw_message = first.get("msg", "")
            stripped = raw_message.removeprefix("Value error, ")
            message = stripped if stripped else (f"Please check the '{field}' field." if field else "Please check your input.")
        return _error_response(message, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("Integrity error on %s: %s", request.url.path, exc)
        return _error_response(
            "This action conflicts with existing data (e.g. a duplicate or linked record).",
            status.HTTP_409_CONFLICT,
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.error("Database error on %s: %s", request.url.path, exc)
        return _error_response(
            "A database error occurred. Please try again.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s", request.url.path)
        return _error_response(
            "Something went wrong. Please try again.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
