# Contributing

## Git flow

We use **GitHub Flow**: `main` is always deployable and every change arrives through a
Pull Request.

1. Branch off the latest `main`.
2. Make small commits that follow the convention below.
3. Open a PR to `main` using the template; at least **one review** is required.
4. Merge only when the **`CI passed`** check is green (lint, secret scan, tests, Docker build).
5. Merging to `main` triggers the **CD** workflow (ECR + ECS).

Delete the branch after merging.

## Branch names

`<type>/<short-kebab-description>` — lowercase, no spaces, in English.

| Type | Use it for | Example |
|---|---|---|
| `feat/` | New functionality | `feat/reviews-api` |
| `fix/` | Bug fixes | `fix/pagination-off-by-one` |
| `refactor/` | Code changes without behavior change | `refactor/review-service-layers` |
| `test/` | Only tests | `test/seed-idempotency` |
| `docs/` | Only documentation | `docs/api-contract` |
| `ci/` | Pipelines and workflows | `ci/github-actions` |
| `build/` | Docker, dependencies | `build/multi-stage-image` |
| `chore/` | Maintenance | `chore/update-ruff` |
| `hotfix/` | Urgent fix on production | `hotfix/db-connection-leak` |

## Commit messages — Conventional Commits

```
<type>(<optional scope>): <imperative summary, lowercase, no period, ≤ 72 chars>

<optional body: what and why, wrapped at 72 chars>

<optional footer: BREAKING CHANGE: ..., Refs #12>
```

Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `ci`, `build`, `chore`, `revert`.
Common scopes: `api`, `seed`, `db`, `catalog`, `docker`, `deps`.

Examples:

```
feat(api): add rating filters to the reviews listing
fix(seed): keep duplicate timestamps in the past
ci: run tests against PostgreSQL service
```

## Recommended branch protection for `main`

Settings → Branches → Add rule for `main`:

- Require a pull request before merging (1 approval).
- Require status checks to pass: **`CI passed`**.
- Require branches to be up to date before merging.
- Block force pushes and deletions.

## Local checks before pushing

```bash
uv run ruff check . && uv run ruff format --check .
uv run pytest --cov
```
