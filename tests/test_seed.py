from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine

from src.core.catalog import get_hotel_ids
from src.models.review_model import Review
from src.seed.__main__ import build_config, parse_args
from src.seed.generator import SeedConfig, generate_day
from src.seed.runner import run_seed

CONFIG = SeedConfig(
    seed=42,
    start_date=date(2026, 9, 1),
    end_date=date(2026, 9, 7),
    reviews_per_day=40,
    duplicate_rate=0.10,
)


def count_reviews(engine: Engine) -> int:
    with engine.connect() as connection:
        return connection.execute(select(func.count()).select_from(Review)).scalar_one()


def snapshot(engine: Engine) -> list[tuple]:
    columns = (Review.platform, Review.external_id, Review.rating, Review.text, Review.hotel_id)
    with engine.connect() as connection:
        return list(connection.execute(select(*columns).order_by(*columns[:2])).all())


def test_same_seed_generates_identical_data() -> None:
    day = date(2026, 9, 15)
    assert generate_day(CONFIG, day) == generate_day(CONFIG, day)


def test_different_seed_generates_different_data() -> None:
    other = SeedConfig(**{**CONFIG.__dict__, "seed": 7})
    day = date(2026, 9, 15)
    assert generate_day(CONFIG, day) != generate_day(other, day)


def test_a_day_is_the_same_regardless_of_the_requested_range() -> None:
    wide = SeedConfig(**{**CONFIG.__dict__, "start_date": date(2026, 1, 1)})
    assert generate_day(wide, date(2026, 9, 3)) == generate_day(CONFIG, date(2026, 9, 3))


def test_generated_rows_are_valid() -> None:
    rows = generate_day(CONFIG, date(2026, 9, 2))
    hotel_ids = get_hotel_ids()
    assert all(1 <= row["rating"] <= 5 for row in rows)
    assert all(row["hotel_id"] in hotel_ids for row in rows)
    assert all(row["stay_date"] < row["published_at"].date() for row in rows)
    keys = [(row["platform"], row["external_id"]) for row in rows]
    assert len(keys) == len(set(keys))


def test_reviews_cover_three_languages() -> None:
    languages = {row["language"] for day in CONFIG.days() for row in generate_day(CONFIG, day)}
    assert languages == {"es", "en", "pt"}


def injected_duplicates(config: SeedConfig) -> tuple[int, int]:
    """Return (originals, duplicates).

    The generator appends each duplicate right after its original: same hotel, stay,
    rating and text (maybe without the final dot) but another platform and id.
    """
    originals = duplicates = 0
    for day in config.days():
        rows = generate_day(config, day)
        for previous, row in zip([None, *rows], rows, strict=False):
            is_duplicate = (
                previous is not None
                and row["platform"] != previous["platform"]
                and (row["hotel_id"], row["stay_date"], row["rating"])
                == (previous["hotel_id"], previous["stay_date"], previous["rating"])
                and row["text"].rstrip(".") == previous["text"].rstrip(".")
            )
            if is_duplicate:
                duplicates += 1
            else:
                originals += 1
    return originals, duplicates


def test_duplicate_rate_zero_injects_no_duplicates() -> None:
    clean = SeedConfig(**{**CONFIG.__dict__, "duplicate_rate": 0.0})
    assert injected_duplicates(clean)[1] == 0


def test_duplicate_rate_is_respected() -> None:
    config = SeedConfig(**{**CONFIG.__dict__, "end_date": date(2026, 9, 30)})
    originals, duplicates = injected_duplicates(config)
    assert 0.07 < duplicates / originals < 0.13  # configured 10 %


def test_duplicates_keep_the_guest_but_vary_the_name_slightly() -> None:
    config = SeedConfig(**{**CONFIG.__dict__, "duplicate_rate": 1.0})
    rows = generate_day(config, date(2026, 9, 1))
    pairs = list(zip(rows[::2], rows[1::2], strict=True))
    assert all(original["platform"] != copy["platform"] for original, copy in pairs)
    assert any(original["reviewer_name"] != copy["reviewer_name"] for original, copy in pairs)
    assert all(copy["published_at"] <= original["published_at"] for original, copy in pairs)


def test_seed_is_idempotent(engine: Engine) -> None:
    first = run_seed(engine, CONFIG)
    assert first.inserted == first.generated > 0
    second = run_seed(engine, CONFIG)
    assert second.inserted == 0
    assert second.skipped == second.generated
    assert count_reviews(engine) == first.generated


def test_seed_is_reproducible(engine: Engine) -> None:
    run_seed(engine, CONFIG)
    before = snapshot(engine)
    with engine.begin() as connection:
        connection.execute(Review.__table__.delete())
    run_seed(engine, CONFIG)
    assert snapshot(engine) == before


def test_dry_run_writes_nothing(engine: Engine) -> None:
    result = run_seed(engine, CONFIG, dry_run=True)
    assert result.generated > 0
    assert count_reviews(engine) == 0


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        ([], (date(2026, 9, 1), date(2026, 9, 30), 20)),
        (["--mode", "full"], (date(2025, 10, 1), date(2026, 9, 30), 300)),
        (["--date", "2026-10-14"], (date(2026, 10, 14), date(2026, 10, 14), 20)),
        (
            ["--start-date", "2026-01-01", "--end-date", "2026-01-31", "--reviews-per-day", "5"],
            (date(2026, 1, 1), date(2026, 1, 31), 5),
        ),
    ],
)
def test_cli_builds_expected_config(argv: list[str], expected: tuple) -> None:
    config = build_config(parse_args(argv))
    assert (config.start_date, config.end_date, config.reviews_per_day) == expected


@pytest.mark.parametrize(
    "kwargs",
    [
        {"start_date": date(2026, 2, 1), "end_date": date(2026, 1, 1)},
        {"reviews_per_day": 0},
        {"duplicate_rate": 1.5},
    ],
)
def test_invalid_seed_config_is_rejected(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        SeedConfig(**{**CONFIG.__dict__, **kwargs})
