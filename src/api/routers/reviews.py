from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from src.api.dependencies import ReviewServiceDep
from src.api.errors import ERROR_RESPONSES
from src.core.config import get_settings
from src.models.review_model import Language, Platform
from src.schemas.review_schema import (
    ReviewCreate,
    ReviewFilters,
    ReviewPage,
    ReviewRead,
    ReviewUpdate,
    SortOrder,
)

settings = get_settings()

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


@router.get(
    "",
    response_model=ReviewPage,
    summary="List reviews (paginated)",
    description=(
        "Paginated list of reviews ordered by publication date. Ingestion jobs call it "
        "daily with `published_from`/`published_to` and walk the pages until `has_next` "
        "is false."
    ),
    responses={422: ERROR_RESPONSES[422]},
)
def list_reviews(
    service: ReviewServiceDep,
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=settings.max_page_size, description="Items per page")
    ] = settings.default_page_size,
    hotel_id: Annotated[str | None, Query(max_length=16, examples=["HP-CO-001"])] = None,
    platform: Platform | None = None,
    language: Language | None = None,
    min_rating: Annotated[int | None, Query(ge=1, le=5)] = None,
    max_rating: Annotated[int | None, Query(ge=1, le=5)] = None,
    published_from: Annotated[date | None, Query(description="Inclusive, UTC")] = None,
    published_to: Annotated[date | None, Query(description="Inclusive, UTC")] = None,
    order: SortOrder = SortOrder.ASC,
) -> ReviewPage:
    filters = ReviewFilters(
        hotel_id=hotel_id,
        platform=platform,
        language=language,
        min_rating=min_rating,
        max_rating=max_rating,
        published_from=published_from,
        published_to=published_to,
    )
    return service.list_reviews(filters, page=page, page_size=page_size, order=order)


@router.get(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Get a review by id",
    responses={404: ERROR_RESPONSES[404]},
)
def get_review(review_id: int, service: ReviewServiceDep) -> ReviewRead:
    return ReviewRead.model_validate(service.get_review(review_id))


@router.post(
    "",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review",
    responses={409: ERROR_RESPONSES[409], 422: ERROR_RESPONSES[422]},
)
def create_review(payload: ReviewCreate, service: ReviewServiceDep) -> ReviewRead:
    return ReviewRead.model_validate(service.create_review(payload))


@router.patch(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Partially update a review",
    responses={404: ERROR_RESPONSES[404], 422: ERROR_RESPONSES[422]},
)
def update_review(review_id: int, payload: ReviewUpdate, service: ReviewServiceDep) -> ReviewRead:
    return ReviewRead.model_validate(service.update_review(review_id, payload))


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a review",
    responses={404: ERROR_RESPONSES[404]},
)
def delete_review(review_id: int, service: ReviewServiceDep) -> Response:
    service.delete_review(review_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
