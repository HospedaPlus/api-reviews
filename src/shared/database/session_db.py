from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from src.core.config import get_settings


def build_engine(database_url: str) -> Engine:
    connect_args: dict = {}
    if database_url.startswith("postgresql"):
        # Always talk UTC with Postgres so the API returns "...Z"-style timestamps
        # no matter the server's (or RDS parameter group's) timezone.
        connect_args["options"] = "-c timezone=UTC"
    return create_engine(
        database_url,
        pool_pre_ping=True,  # drop dead connections after RDS failover / idle timeouts
        connect_args=connect_args,
    )


engine: Engine = build_engine(get_settings().database_url)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
