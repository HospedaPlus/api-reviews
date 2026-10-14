## Summary

<!-- What does this PR change and why? Link the issue/ticket if there is one. -->

## Type of change

- [ ] `feat` — new feature
- [ ] `fix` — bug fix
- [ ] `refactor` / `perf` — no behavior change
- [ ] `test` / `docs` / `ci` / `build` / `chore`

## Business rules / requirements touched

<!-- e.g. RN-10 (reputation score), RN-11 (PII), RF-08, CT-06 (seed) -->

## How was it tested?

- [ ] `uv run ruff check . && uv run ruff format --check .`
- [ ] `uv run pytest --cov`
- [ ] `docker compose up --build` works from a clean state
- [ ] New migration created with `alembic revision --autogenerate` and reviewed (if models changed)

## Checklist

- [ ] Branch and commits follow [CONTRIBUTING.md](../CONTRIBUTING.md)
- [ ] No credentials, keys or `.env` files committed
- [ ] README / OpenAPI docs updated if the contract changed
