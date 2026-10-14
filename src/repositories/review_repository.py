from datetime import UTC, datetime, time, timedelta

from sqlalchemy import func
from sqlmodel import Session, col, select
from sqlmodel.sql.expression import SelectOfScalar

from src.models.review_model import Platform, Review
from src.schemas.review_schema import ReviewFilters, SortOrder


class ReviewRepository:
    """Data access for reviews. No business rules here, only queries."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, review_id: int) -> Review | None:
        return self.session.get(Review, review_id)

    def get_by_external_id(self, platform: Platform, external_id: str) -> Review | None:
        statement = select(Review).where(
            Review.platform == platform, Review.external_id == external_id
        )
        return self.session.exec(statement).one_or_none()

    def list(
        self, filters: ReviewFilters, offset: int, limit: int, order: SortOrder
    ) -> tuple[list[Review], int]:
        statement = self._apply_filters(select(Review), filters)
        count_statement = self._apply_filters(select(func.count()).select_from(Review), filters)

        total = self.session.exec(count_statement).one()

        if order is SortOrder.DESC:
            statement = statement.order_by(col(Review.published_at).desc(), col(Review.id).desc())
        else:
            # Stable ordering (published_at, id) so pages never overlap or skip rows.
            statement = statement.order_by(col(Review.published_at), col(Review.id))

        items = self.session.exec(statement.offset(offset).limit(limit)).all()
        return list(items), total

    def add(self, review: Review) -> Review:
        self.session.add(review)
        self.session.commit()
        self.session.refresh(review)
        return review

    def delete(self, review: Review) -> None:
        self.session.delete(review)
        self.session.commit()

    @staticmethod
    def _apply_filters(statement: SelectOfScalar, filters: ReviewFilters) -> SelectOfScalar:
        if filters.hotel_id:
            statement = statement.where(Review.hotel_id == filters.hotel_id)
        if filters.platform:
            statement = statement.where(Review.platform == filters.platform)
        if filters.language:
            statement = statement.where(Review.language == filters.language)
        if filters.min_rating is not None:
            statement = statement.where(Review.rating >= filters.min_rating)
        if filters.max_rating is not None:
            statement = statement.where(Review.rating <= filters.max_rating)
        if filters.published_from:
            start = datetime.combine(filters.published_from, time.min, tzinfo=UTC)
            statement = statement.where(Review.published_at >= start)
        if filters.published_to:
            # Inclusive end date: everything before the next day at 00:00 UTC.
            end = datetime.combine(filters.published_to + timedelta(days=1), time.min, tzinfo=UTC)
            statement = statement.where(Review.published_at < end)
        return statement
