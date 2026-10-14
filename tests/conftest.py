"""Test fixtures.

By default the tests use an in-memory SQLite database (fast, nothing to install).
CI also runs them against a real PostgreSQL service by setting TEST_DATABASE_URL.
"""

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from src.main import app
from src.shared.database.session_db import build_engine, get_session

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite://")


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    if TEST_DATABASE_URL.startswith("sqlite"):
        test_engine = create_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        test_engine = build_engine(TEST_DATABASE_URL)
    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    SQLModel.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(engine: Engine) -> Iterator[None]:
    yield
    with engine.begin() as connection:
        for table in reversed(SQLModel.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as db_session:
        yield db_session


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    def override_get_session() -> Iterator[Session]:
        with Session(engine) as db_session:
            yield db_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def review_payload() -> dict:
    return {
        "external_id": "BK-test-0001",
        "platform": "booking",
        "hotel_id": "HP-CO-001",
        "language": "es",
        "rating": 4,
        "title": "Muy buena estadía",
        "text": "El personal fue muy amable y la habitación estaba limpia.",
        "reviewer_name": "María López",
        "reviewer_country": "co",
        "stay_date": "2026-10-01",
        "published_at": "2026-10-05T12:00:00Z",
    }
