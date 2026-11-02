"""Seed CLI.

Examples:
    python -m src.seed                          # dev mode (30 days x ~20 reviews/day)
    python -m src.seed --mode full              # full mode (365 days x ~300 reviews/day)
    python -m src.seed --date 2026-10-14        # one daily batch (what a daily job would call)
    python -m src.seed --duplicate-rate 0.10    # inject more cross-platform duplicates
    python -m src.seed --mode full --end-date today   # initial load: last 365 days up to now
    python -m src.seed --live                   # keep publishing today's reviews (simulator)

Every option can also be set with an environment variable (SEED_MODE, SEED_VALUE,
SEED_END_DATE, SEED_DUPLICATE_RATE, ...). The command reads DATABASE_URL, so the same
script runs locally and against RDS.
"""

import argparse
import logging
import os
import time
from datetime import UTC, date, datetime, timedelta

from src.seed.generator import SeedConfig

MODES = {
    "dev": {"days": 30, "reviews_per_day": 20},
    "full": {"days": 365, "reviews_per_day": 300},
}
DEFAULT_SEED = 42
# Fixed default so two runs on different days still produce exactly the same data.
DEFAULT_END_DATE = "2026-09-30"
DEFAULT_DUPLICATE_RATE = 0.05


def parse_day(value: str) -> date:
    """YYYY-MM-DD, or 'today' / 'yesterday' (UTC)."""
    today = datetime.now(UTC).date()
    if value == "today":
        return today
    if value == "yesterday":
        return today - timedelta(days=1)
    return date.fromisoformat(value)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the F5 reviews database.")
    parser.add_argument("--mode", choices=MODES, default=os.getenv("SEED_MODE", "dev"))
    parser.add_argument("--seed", type=int, default=int(os.getenv("SEED_VALUE", DEFAULT_SEED)))
    parser.add_argument(
        "--end-date",
        type=parse_day,
        default=parse_day(os.getenv("SEED_END_DATE", DEFAULT_END_DATE)),
        help="Last day generated: YYYY-MM-DD or 'today' (then only reviews published until now)",
    )
    parser.add_argument(
        "--start-date",
        type=date.fromisoformat,
        default=os.getenv("SEED_START_DATE"),
        help="Defaults to end-date minus the number of days of the mode",
    )
    parser.add_argument(
        "--date",
        type=parse_day,
        help="Generate a single day (overrides start/end date). Use 'today' via shell date.",
    )
    parser.add_argument(
        "--reviews-per-day",
        type=int,
        default=os.getenv("SEED_REVIEWS_PER_DAY"),
        help="Overrides the mode's daily volume",
    )
    parser.add_argument(
        "--duplicate-rate",
        type=float,
        default=float(os.getenv("SEED_DUPLICATE_RATE", DEFAULT_DUPLICATE_RATE)),
        help="Share of reviews also published on a second platform (0-1)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Generate without writing")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Simulator: every few minutes insert the reviews already 'published' today",
    )
    parser.add_argument(
        "--live-interval-minutes",
        type=float,
        default=float(os.getenv("SEED_LIVE_INTERVAL_MINUTES", "15")),
    )
    parser.add_argument(
        "--live-catchup-days",
        type=int,
        default=int(os.getenv("SEED_LIVE_CATCHUP_DAYS", "3")),
        help="Live mode also completes the previous N days (e.g. after the container was down)",
    )
    parser.add_argument(
        "--live-start-date",
        type=parse_day,
        default=parse_day(os.environ["SEED_LIVE_START_DATE"])
        if os.getenv("SEED_LIVE_START_DATE")
        else None,
        help="Live mode never generates days before this one (e.g. 'start publishing today')",
    )
    return parser.parse_args(argv)


def build_config(args: argparse.Namespace) -> SeedConfig:
    mode = MODES[args.mode]
    if args.date:
        start, end = args.date, args.date
    else:
        end = args.end_date
        start = (
            date.fromisoformat(str(args.start_date))
            if args.start_date
            else end - timedelta(days=mode["days"] - 1)
        )
    now = datetime.now(UTC)
    return SeedConfig(
        seed=args.seed,
        start_date=start,
        end_date=end,
        reviews_per_day=int(args.reviews_per_day or mode["reviews_per_day"]),
        duplicate_rate=args.duplicate_rate,
        # A day that is not over yet only gets the reviews published so far.
        cutoff=now if end >= now.date() else None,
    )


def live_config(args: argparse.Namespace, now: datetime) -> SeedConfig:
    """Today (up to now) plus the previous catch-up days."""
    mode = MODES[args.mode]
    return SeedConfig(
        seed=args.seed,
        start_date=max(
            now.date() - timedelta(days=args.live_catchup_days),
            args.live_start_date or date.min,
        ),
        end_date=now.date(),
        reviews_per_day=int(args.reviews_per_day or mode["reviews_per_day"]),
        duplicate_rate=args.duplicate_rate,
        cutoff=now,
    )


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    config = build_config(args)

    # Imported here so --help works without a database configured.
    from src.seed.runner import run_seed
    from src.shared.database.session_db import engine

    log = logging.getLogger("seed")
    if not args.live:
        log.info("Seeding with %s (mode=%s)", config, args.mode)
        run_seed(engine, config, dry_run=args.dry_run)
        return

    # Live simulator: same deterministic reviews, revealed as their published_at passes.
    # Idempotent (ON CONFLICT DO NOTHING), so every pass only adds the new ones.
    log.info("Live mode every %s min (mode=%s)", args.live_interval_minutes, args.mode)
    while True:
        try:
            run_seed(engine, live_config(args, datetime.now(UTC)), dry_run=args.dry_run)
        except Exception:  # keep the simulator alive; the next pass retries
            log.exception("Live pass failed")
        time.sleep(args.live_interval_minutes * 60)


if __name__ == "__main__":
    main()
