# Repository Guidelines

## Project Structure & Module Organization

- `backend/`: Flask + SQLModel API service.
  - `backend/api/v1/`: REST endpoints (blueprints/routes).
  - `backend/models/`: SQLModel table models.
  - `backend/services/`: business logic and queries.
  - `backend/utils/`: shared helpers (e.g. response envelope).
- `frontend/`: Umi (`@umijs/max`) React + TypeScript UI.
  - `frontend/src/pages/`: route pages (Dashboard/Accounts/Products/Snapshots…).
  - `frontend/src/services/`: API clients and typed request/response wrappers.
  - `frontend/src/types/`: shared TS types.
- `doc/`: sprint plans/PRD and reviews.
- `openapi.yaml`: API contract (treat as the source of truth).

## Build, Test, and Development Commands

Frontend (from `frontend/`):
- `npm install`: install dependencies.
- `npm run dev`: start local dev server.
- `npm run build`: production build.
- `npm run format`: run Prettier on the repo.

Backend (from `backend/`):
- `python run.py`: start the API server (default port 5000).
- Dependency note: both `pyproject.toml` and `requirements.txt` exist; keep them consistent (prefer one workflow per environment).

## Coding Style & Naming Conventions

- **Encoding**: all repository text files must be **UTF-8** (never GBK/GB2312).
- Python: 4-space indentation; keep route handlers thin and push logic into `services/`.
- TypeScript/React: 2-space indentation (Prettier-managed); keep API calls inside `src/services/`.
- Naming:
  - API routes: `/api/...` under `backend/api/v1/`.
  - Models: singular class names in `backend/models/` (e.g. `Account`, `Product`).

## Testing Guidelines

- No dedicated automated test suite is currently present.
- If adding tests:
  - Backend: add `pytest` and place tests under `backend/tests/`.
  - Frontend: add a runner (e.g. Vitest/Jest) and place tests under `frontend/src/**/__tests__/`.

## Commit & Pull Request Guidelines

- Commit subjects currently follow sprint-style messages (e.g. `Sprint 1: ...`, `sprint1&2 review and bugfix`). Keep subjects short and scoped.
- PRs should include:
  - What changed and why, linked to a Sprint/doc item when applicable (`doc/sprint*.md`).
  - Contract impact: update `openapi.yaml` for any API/field changes.
  - Screenshots/GIFs for UI changes (Dashboard/Products/Snapshots pages).

## Security & Repo Hygiene

- Do **not** commit generated artifacts or environments (e.g. `frontend/node_modules/`, `frontend/src/.umi/`, `backend/.venv/`, `**/__pycache__/`).
- Prefer structured logging over `print` and avoid leaking sensitive data in error messages.

