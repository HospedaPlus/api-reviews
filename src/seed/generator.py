"""Deterministic generator of synthetic reviews.

Every day is generated with its own RNG seeded by ``"<seed>:<YYYY-MM-DD>"``. That gives:

* Reproducibility: same seed + same parameters -> exactly the same rows.
* Stable natural keys: a review keeps its ``external_id`` no matter which date range
  is requested, so daily runs and full backfills never disagree.
* Idempotency: rows are inserted with ``ON CONFLICT (platform, external_id) DO NOTHING``.
"""

import random
import unicodedata
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from src.core.catalog import Hotel, get_hotels
from src.seed import texts

NAMESPACE = uuid.UUID("6f1c3c3e-4b4e-4f0a-9a57-5f2b8d1e0f05")  # fixed namespace for uuid5

PLATFORM_WEIGHTS: dict[str, float] = {
    "booking": 0.40,
    "google": 0.30,
    "tripadvisor": 0.20,
    "expedia": 0.10,
}
PLATFORM_PREFIX = {"booking": "BK", "google": "GG", "tripadvisor": "TA", "expedia": "EX"}

LANGUAGE_WEIGHTS_BY_COUNTRY: dict[str, dict[str, float]] = {
    "CO": {"es": 0.75, "en": 0.20, "pt": 0.05},
    "MX": {"es": 0.70, "en": 0.27, "pt": 0.03},
    "ES": {"es": 0.65, "en": 0.30, "pt": 0.05},
    "BR": {"pt": 0.75, "en": 0.15, "es": 0.10},
    "PT": {"pt": 0.60, "en": 0.30, "es": 0.10},
}

RESORT_ONLY_TOPICS = {"pool"}


@dataclass(frozen=True)
class SeedConfig:
    seed: int
    start_date: date
    end_date: date
    reviews_per_day: int
    duplicate_rate: float = 0.05

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        if self.reviews_per_day < 1:
            raise ValueError("reviews_per_day must be >= 1")
        if not 0.0 <= self.duplicate_rate <= 1.0:
            raise ValueError("duplicate_rate must be between 0 and 1")

    def days(self) -> Iterator[date]:
        current = self.start_date
        while current <= self.end_date:
            yield current
            current += timedelta(days=1)


def hotel_quality(seed: int, hotel: Hotel) -> float:
    """Average rating of a hotel (3.2-4.6), fixed per seed so trends are consistent."""
    return random.Random(f"{seed}:quality:{hotel.hotel_id}").uniform(3.2, 4.6)


def _weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    return rng.choices(list(weights), weights=list(weights.values()), k=1)[0]


def _sentiment(rating: int) -> str:
    if rating >= 4:
        return "positive"
    if rating == 3:
        return "mixed"
    return "negative"


def _external_id(platform: str, seed: int, day: date, index: int, suffix: str = "") -> str:
    token = uuid.uuid5(NAMESPACE, f"{seed}:{day.isoformat()}:{index}{suffix}").hex[:16]
    return f"{PLATFORM_PREFIX[platform]}-{token}"


def _build_text(rng: random.Random, language: str, rating: int, hotel: Hotel) -> str:
    sentiment = _sentiment(rating)
    topics = [t for t in texts.TOPICS if hotel.type == "resort" or t not in RESORT_ONLY_TOPICS]
    chosen = rng.sample(topics, k=rng.randint(1, 3))

    phrases = [rng.choice(texts.OPENERS[sentiment][language])]
    for topic in chosen:
        positive, negative = texts.TOPICS[topic][language]
        if sentiment == "positive":
            phrases.append(positive)
        elif sentiment == "negative":
            phrases.append(negative)
        else:
            phrases.append(rng.choice((positive, negative)))
    return " ".join(phrases)


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _name_variant(rng: random.Random, name: str) -> str:
    """Slight differences a guest's name shows on another platform."""
    first, last = name.split(" ", 1)
    variants = (
        _strip_accents(name),
        name.lower(),
        f"{first} {last[0]}.",
        name.upper(),
    )
    return rng.choice(variants)


def generate_day(config: SeedConfig, day: date) -> list[dict]:
    rng = random.Random(f"{config.seed}:{day.isoformat()}")
    hotels = get_hotels()
    hotel_weights = [hotel.rooms for hotel in hotels]  # bigger hotels get more reviews

    # +/-15 % daily variation around the configured volume
    count = max(1, round(config.reviews_per_day * rng.uniform(0.85, 1.15)))
    day_start = datetime.combine(day, time.min, tzinfo=UTC)
    rows: list[dict] = []

    for index in range(count):
        hotel = rng.choices(hotels, weights=hotel_weights, k=1)[0]
        platform = _weighted_choice(rng, PLATFORM_WEIGHTS)
        language = _weighted_choice(rng, LANGUAGE_WEIGHTS_BY_COUNTRY[hotel.country])
        rating = min(5, max(1, round(rng.gauss(hotel_quality(config.seed, hotel), 0.9))))
        name = f"{rng.choice(texts.FIRST_NAMES[language])} {rng.choice(texts.LAST_NAMES[language])}"
        published_at = day_start + timedelta(seconds=rng.randint(0, 86_399))
        stay_date = day - timedelta(days=rng.randint(1, 21))

        review = {
            "external_id": _external_id(platform, config.seed, day, index),
            "platform": platform,
            "hotel_id": hotel.hotel_id,
            "language": language,
            "rating": rating,
            "title": rng.choice(texts.TITLES[_sentiment(rating)][language]),
            "text": _build_text(rng, language, rating, hotel),
            "reviewer_name": name,
            "reviewer_country": rng.choice(texts.REVIEWER_COUNTRIES[language]),
            "stay_date": stay_date,
            "published_at": published_at,
            # Seeded rows "appear" when published: keeps the seed fully reproducible.
            "created_at": published_at,
            "updated_at": published_at,
        }
        rows.append(review)

        # Data-quality defect: the same guest posts the same review on another platform.
        if rng.random() < config.duplicate_rate:
            other_platforms = [p for p in PLATFORM_WEIGHTS if p != platform]
            dup_platform = rng.choice(other_platforms)
            dup_published = published_at - timedelta(seconds=rng.randint(0, 30 * 3600))
            rows.append(
                {
                    **review,
                    "external_id": _external_id(dup_platform, config.seed, day, index, ":dup"),
                    "platform": dup_platform,
                    "reviewer_name": _name_variant(rng, name),
                    "text": review["text"] if rng.random() < 0.5 else review["text"].rstrip("."),
                    "published_at": dup_published,
                    "created_at": dup_published,
                    "updated_at": dup_published,
                }
            )
    return rows


def generate(config: SeedConfig) -> Iterator[list[dict]]:
    """Yield the reviews of each day in the configured range."""
    for day in config.days():
        yield generate_day(config, day)
