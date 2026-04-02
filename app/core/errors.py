from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ImageValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(code="image_validation_error", message=message, status_code=422)


class InferenceServiceError(AppError):
    def __init__(self, message: str = "Inference service is unavailable") -> None:
        super().__init__(code="inference_service_error", message=message, status_code=503)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
        )
