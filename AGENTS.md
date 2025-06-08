# PantryPal Codex Guide

This file provides guidelines for Codex agents working on this repository.

## Repository Structure

- `api/` – FastAPI backend service. Important modules:
  - `app.py` – application entrypoint registering all routers.
  - `pantry/` – pantry item CRUD and ROI calculations.
  - `macros/` – USDA food API integration for macro enrichment.
  - `auth/` – authentication logic using AWS Cognito.
  - `ai/` – OpenAI helpers for recipes and images.
  - `storage/` – DynamoDB utilities.
  - `tests/` – Pytest suite for the backend.
- `expo/ppal/` – Expo + React Native front‑end.
- `docs/` – architecture diagrams and screenshots.
- `setup.sh` – installs Python and npm dependencies.

## Working with the Backend

Activate the virtual environment under `api/.venv` and run the server:

```bash
cd api
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
uvicorn app:app --reload --port 8000
```

Key environment variables expected by the API include:
`PANTRY_TABLE_NAME`, `AUTH_TABLE_NAME`, `USDA_API_KEY`, `OPENAI_API_KEY`,
`SECRET_KEY`, `MACRO_QUEUE_URL`, and `IMAGE_QUEUE_URL`.

## Working with the Frontend

From `expo/ppal` run the Expo dev server:

```bash
npm start
```

## Testing

Python tests live in `api/tests`. Run the full suite from the repo root:

```bash
pytest
```

Tests rely on FastAPI dependency overrides and do not require AWS credentials.

## Conventions

- Keep backend code under `api` and frontend code under `expo/ppal`.
- When adding a new API route, create a router module and register it in `api/app.py`.
- Run `pytest` after modifying backend code.
- Commit descriptive messages to make future updates easy to track.

