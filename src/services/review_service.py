import math
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from src.core.catalog import get_hotel_ids
from src.core.errors import BusinessRuleError, ConflictError, NotFoundError
from src.models.review_model import Review, utc_now
from src.repositories.review_repository import ReviewRepository
from src.schemas.review_schema import (
    Page,
    ReviewCreate,
    ReviewFilters,
    ReviewPage,
    ReviewRead,
    ReviewUpdate,
    SortOrder,
)


class ReviewService:
    def __init__(self, repository: ReviewRepository) -> None:
        self.repository = repository

    def list_reviews(
        self, filters: ReviewFilters, page: int, page_size: int, order: SortOrder
    ) -> ReviewPage:
        if (
            filters.published_from
            and filters.published_to
            and filters.published_from > filters.published_to
        ):
            raise BusinessRuleError("published_from must be on or before published_to")
        if (
            filters.min_rating is not None
            and filters.max_rating is not None
            and filters.min_rating > filters.max_rating
        ):
            raise BusinessRuleError("min_rating must be less than or equal to max_rating")

        items, total = self.repository.list(
            filters, offset=(page - 1) * page_size, limit=page_size, order=order
        )
        total_pages = math.ceil(total / page_size) if total else 0
        return ReviewPage(
            items=[ReviewRead.model_validate(item) for item in items],
            pagination=Page(
                page=page,
                page_size=page_size,
                total_items=total,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1,
            ),
        )

    def get_review(self, review_id: int) -> Review:
        review = self.repository.get(review_id)
        if review is None:
            raise NotFoundError(f"Review {review_id} not found")
        return review

    def create_review(self, data: ReviewCreate) -> Review:
        if data.hotel_id not in get_hotel_ids():
            raise BusinessRuleError(f"Unknown hotel_id '{data.hotel_id}'")
        if data.published_at.tzinfo is None:
            data.published_at = data.published_at.replace(tzinfo=UTC)
        if data.published_at > datetime.now(UTC):
            raise BusinessRuleError("published_at cannot be in the future")
        if data.stay_date and data.stay_date > data.published_at.date():
            raise BusinessRuleError("stay_date cannot be after published_at")

        if self.repository.get_by_external_id(data.platform, data.external_id):
            raise ConflictError(
                f"Review '{data.external_id}' already exists on platform '{data.platform}'"
            )
        try:
            return self.repository.add(Review(**data.model_dump()))
        except IntegrityError as error:
            # Two concurrent inserts can both pass the check above; the unique
            # constraint is the real guarantee.
            self.repository.session.rollback()
            raise ConflictError(
                f"Review '{data.external_id}' already exists on platform '{data.platform}'"
            ) from error

    def update_review(self, review_id: int, data: ReviewUpdate) -> Review:
        review = self.get_review(review_id)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            raise BusinessRuleError("At least one field must be provided")
        for field, value in changes.items():
            if value is None and field in {"language", "rating", "text"}:
                raise BusinessRuleError(f"'{field}' cannot be null")
            setattr(review, field, value)
        review.updated_at = utc_now()
        return self.repository.add(review)

    def delete_review(self, review_id: int) -> None:
        review = self.get_review(review_id)
        self.repository.delete(review)
