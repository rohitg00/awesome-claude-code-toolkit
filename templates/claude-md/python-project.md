# DataFlow Pipeline

ETL pipeline for ingesting, transforming, and serving analytics data from multiple sources.

## Stack
- **Language**: Python 3.12
- **Framework**: FastAPI 0.115 (API), Celery 5.4 (workers)
- **Database**: PostgreSQL 16 (warehouse), Redis 7 (broker/cache)
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **Data**: Pandas 2.2, Polars 1.x, DuckDB (analytics queries)
- **Testing**: pytest, pytest-asyncio, factory-boy, hypothesis
- **Linting**: Ruff (linter + formatter), mypy (strict mode)
- **Package Manager**: uv (lockfile: `uv.lock`)
- **CI/CD**: GitHub Actions, Docker, AWS ECS
- **Docs**: Sphinx with autodoc

## Commands
- `uv sync` - Install dependencies from lockfile
- `uv run fastapi dev` - Start API server (localhost:8000)
- `uv run celery -A dataflow.worker worker --loglevel=info` - Start Celery worker
- `uv run pytest` - Run test suite
- `uv run pytest --cov=dataflow --cov-report=html` - Run tests with coverage
- `uv run mypy dataflow/` - Type check
- `uv run ruff check dataflow/` - Lint
- `uv run ruff format dataflow/` - Format
- `uv run alembic upgrade head` - Apply database migrations
- `uv run alembic revision --autogenerate -m "description"` - Generate migration
- `docker compose up -d` - Start PostgreSQL, Redis, and worker locally

## Project Structure
```
dataflow/
  api/
    routes/           - FastAPI route modules (one per resource)
    deps.py           - Dependency injection (db session, current user, services)
    middleware.py     - CORS, timing, error handling middleware
  core/
    config.py         - Pydantic Settings with environment validation
    security.py       - JWT token handling, password hashing
    exceptions.py     - Custom exception classes with error codes
  models/             - SQLAlchemy ORM models
  schemas/            - Pydantic request/response schemas
  repositories/       - Data access layer (one per model)
  services/           - Business logic (orchestrates repositories)
  workers/
    tasks.py          - Celery task definitions
    pipelines/        - ETL pipeline definitions (extract, transform, load)
  utils/              - Pure utility functions
tests/
  conftest.py         - Shared fixtures (db session, client, factories)
  factories/          - factory-boy model factories
  unit/               - Unit tests for services and utils
  integration/        - Integration tests for repositories and API
alembic/
  versions/           - Migration scripts
  env.py              - Alembic environment configuration
scripts/              - Operational scripts (backfill, cleanup, reports)
```

## Conventions

### Code Style
- Type hints on all function signatures. Use `from __future__ import annotations`.
- Use `Annotated` types with `Depends()` for FastAPI dependency injection.
- Use `async def` for all API endpoints. Use `def` for CPU-bound Celery tasks.
- Prefer `Polars` for new data transformations. Use `Pandas` only for library compatibility.
- Maximum function length: 30 lines. Extract helpers with descriptive names.
- No mutable default arguments. Use `None` with `if arg is None: arg = []`.

### Error Handling
- Custom exceptions inherit from `DataFlowError` base class.
- Services raise domain exceptions (`UserNotFoundError`, `PipelineFailedError`).
- API layer catches domain exceptions and maps to HTTP responses.
- Celery tasks use `autoretry_for` with exponential backoff for transient failures.
- Log all exceptions with full context (task ID, user ID, input parameters).

### Testing
- 85% minimum coverage. 95% on `services/` and `core/`.
- Use `factory-boy` for test data. No raw model construction in tests.
- Use `hypothesis` for property-based tests on data transformation functions.
- Integration tests run against a real PostgreSQL instance (Docker in CI).
- Async tests use `pytest-asyncio` with `asyncio_mode = "auto"`.

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string (`postgresql+asyncpg://...`)
- `REDIS_URL` - Redis connection for Celery broker and result backend
- `SECRET_KEY` - JWT signing key (256-bit random)
- `CORS_ORIGINS` - Comma-separated allowed origins
- `S3_BUCKET` - Data lake bucket for raw ingestion files
- `SENTRY_DSN` - Error tracking
- `LOG_LEVEL` - Logging level (default: `INFO`)

## Key Decisions
| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-06-01 | uv over Poetry | Faster installs, better lockfile resolution |
| 2025-07-15 | Polars over Pandas | 10x faster for column operations, no GIL issues |
| 2025-08-01 | SQLAlchemy 2.0 | Async support, modern mapped_column syntax |
| 2025-09-10 | DuckDB for analytics | In-process OLAP queries, no separate cluster needed |
| 2025-11-01 | Ruff over Black+isort+flake8 | Single tool, faster, consistent configuration |
