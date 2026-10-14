from typing import Annotated

from fastapi import Depends

from src.repositories.review_repository import ReviewRepository
from src.services.review_service import ReviewService
from src.shared.database.session_db import SessionDep


def get_review_service(session: SessionDep) -> ReviewService:
    return ReviewService(ReviewRepository(session))


ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]
