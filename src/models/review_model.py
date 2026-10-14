from datetime import UTC, date, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, Index, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class Platform(StrEnum):
    BOOKING = "booking"
    GOOGLE = "google"
    TRIPADVISOR = "tripadvisor"
    EXPEDIA = "expedia"


class Language(StrEnum):
    ES = "es"
    EN = "en"
    PT = "pt"


def enum_column(enum_cls: type[StrEnum], name: str) -> SAEnum:
    """Store the enum *values* ("booking") instead of the member names ("BOOKING")."""
    return SAEnum(enum_cls, name=name, values_callable=lambda members: [m.value for m in members])


class Review(SQLModel, table=True):
    """A guest review as published on an external platform."""

    __tablename__ = "reviews"
    __table_args__ = (
        # A platform never repeats its own review id -> natural key used by the idempotent seed.
        UniqueConstraint("platform", "external_id", name="uq_reviews_platform_external_id"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),
        # Main access path of the paginated API: filter by hotel, order by publication date.
        Index("ix_reviews_hotel_published", "hotel_id", "published_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    external_id: str = Field(max_length=64)
    platform: Platform = Field(sa_type=enum_column(Platform, "review_platform"))
    hotel_id: str = Field(max_length=16, index=True)
    language: Language = Field(sa_type=enum_column(Language, "review_language"))
    rating: int
    title: str | None = Field(default=None, max_length=150)
    text: str
    reviewer_name: str = Field(max_length=120)
    reviewer_country: str | None = Field(default=None, max_length=2)
    stay_date: date | None = None
    published_at: datetime = Field(sa_type=DateTime(timezone=True), index=True)
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
