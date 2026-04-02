# nn-backend

Backend service for **NoodNood** plate-level nutrition estimation.

This FastAPI app accepts an uploaded food image, validates it, forwards it to an
inference service, and returns estimated nutrition values:

- calories
- protein
- carbs
- fat

## Architecture

Project MVP:

- API layer: route handlers and request/response contracts
- Service layer: prediction orchestration and image validation
- Integration layer: outbound inference client
- Core layer: configuration, logging, and error handling

This keeps the code simple now while making future migration to a more advanced
domain/application/infrastructure layout incremental instead of a rewrite.

## Requirements

- Python 3.11+
- A virtual environment (`.venv` recommended)

## Quick Start

1) Install dependencies:

```bash
.venv/bin/pip install -r requirements.txt
```

2) Create local env file:

```bash
cp .env.example .env
```

3) Run the API:

```bash
.venv/bin/uvicorn app.main:app --reload
```

4) Open docs:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints (MVP)

- `GET /api/v1/health`
  - returns service health status
- `POST /api/v1/predict`
  - accepts multipart image upload (`file`)
  - returns nutrition estimation payload

## Configuration

Environment variables are managed via `app/core/config.py` and `.env`.

Key variables:

- `APP_NAME`
- `APP_ENV`
- `APP_DEBUG`
- `API_PREFIX`
- `MAX_IMAGE_SIZE_BYTES`
- `INFERENCE_BASE_URL`
- `INFERENCE_PREDICT_PATH`
- `INFERENCE_TIMEOUT_SECONDS`

See `.env.example` for defaults.

## Testing


## Notes

- Business logic is kept out of route handlers.
- Inference integration is isolated in a client module for easier replacement.
- Logging includes request latency and request ID to support future observability.