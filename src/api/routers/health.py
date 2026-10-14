from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.shared.database.session_db import SessionDep

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe (used by the ALB / ECS health check)")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness probe (checks the database connection)")
def readiness(session: SessionDep) -> dict[str, str]:
    try:
        session.connection().execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable"
        ) from error
    return {"status": "ready", "database": "ok"}
