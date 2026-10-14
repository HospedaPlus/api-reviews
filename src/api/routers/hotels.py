from fastapi import APIRouter

from src.core.catalog import get_hotels
from src.schemas.review_schema import HotelRead

router = APIRouter(prefix="/api/v1/hotels", tags=["hotels"])


@router.get("", response_model=list[HotelRead], summary="Hotel catalog used by the reviews")
def list_hotels() -> list[HotelRead]:
    return [HotelRead.model_validate(hotel, from_attributes=True) for hotel in get_hotels()]
