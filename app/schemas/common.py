from pydantic import BaseModel


class HealthResponse(BaseModel):
    ok: bool = True
    status: str = "healthy"


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    ok: bool = False
    error: ErrorDetail
