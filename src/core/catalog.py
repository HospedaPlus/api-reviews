"""Hotel catalog shared with the other HospedaPlus sources (F2, F3, F4).

The catalog is versioned as JSON so every simulated source uses the same hotel codes.
HP-PT-001 and HP-PT-002 are the two Portuguese hotels of the Kaggle history (F1).
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parent.parent / "catalog" / "hotels.json"


@dataclass(frozen=True)
class Hotel:
    hotel_id: str
    name: str
    city: str
    country: str
    timezone: str
    type: str
    rooms: int
    source: str


@lru_cache
def get_hotels() -> tuple[Hotel, ...]:
    raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return tuple(Hotel(**item) for item in raw)


@lru_cache
def get_hotel_ids() -> frozenset[str]:
    return frozenset(hotel.hotel_id for hotel in get_hotels())
