from datetime import date, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from src.models.review_model import Language, Platform

Rating = Annotated[int, Field(ge=1, le=5, description="Normalized rating on a 1-5 scale")]
HotelId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=16)]
CountryCode = Annotated[
    str, StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Za-z]{2}$")
]


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class ReviewCreate(BaseModel):
    external_id: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)
    ]
    platform: Platform
    hotel_id: HotelId
    language: Language
    rating: Rating
    title: Annotated[str, StringConstraints(strip_whitespace=True, max_length=150)] | None = None
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
    reviewer_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ]
    reviewer_country: CountryCode | None = None
    stay_date: date | None = None
    published_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "external_id": "BK-8f14e45f",
                "platform": "booking",
                "hotel_id": "HP-CO-001",
                "language": "es",
                "rating": 4,
                "title": "Muy buena estadia",
                "text": "El personal fue muy amable y la habitacion estaba limpia.",
                "reviewer_name": "Maria Lopez",
                "reviewer_country": "CO",
                "stay_date": "2026-10-10",
                "published_at": "2026-10-13T15:20:00Z",
            }
        }
    )


class ReviewUpdate(BaseModel):
    """Partial update (PATCH). Platform, external id and hotel are immutable."""

    language: Language | None = None
    rating: Rating | None = None
    title: Annotated[str, StringConstraints(strip_whitespace=True, max_length=150)] | None = None
    text: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
        | None
    ) = None


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    platform: Platform
    hotel_id: str
    language: Language
    rating: int
    title: str | None
    text: str
    reviewer_name: str
    reviewer_country: str | None
    stay_date: date | None
    published_at: datetime
    created_at: datetime
    updated_at: datetime


class ReviewFilters(BaseModel):
    hotel_id: str | None = None
    platform: Platform | None = None
    language: Language | None = None
    min_rating: int | None = None
    max_rating: int | None = None
    published_from: date | None = None
    published_to: date | None = None


class Page(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ReviewPage(BaseModel):
    items: list[ReviewRead]
    pagination: Page


class HotelRead(BaseModel):
    hotel_id: str
    name: str
    city: str
    country: str
    timezone: str
    type: str
    rooms: int
