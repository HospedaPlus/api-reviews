"""Seed CLI.

Examples:
    python -m src.seed                          # dev mode (30 days x ~20 reviews/day)
    python -m src.seed --mode full              # full mode (365 days x ~300 reviews/day)
    python -m src.seed --date 2026-10-14        # one daily batch (what a daily job would call)
    python -m src.seed --duplicate-rate 0.10    # inject more cross-platform duplicates

Every option can also be set with an environment variable (SEED_MODE, SEED_VALUE,
SEED_END_DATE, SEED_DUPLICATE_RATE, ...). The command reads DATABASE_URL, so the same
script runs locally and against RDS.
"""

import argparse
import logging
import os
from datetime import date, timedelta

from src.seed.generator import SeedConfig

MODES = {
    "dev": {"days": 30, "reviews_per_day": 20},
    "full": {"days": 365, "reviews_per_day": 300},
}
DEFAULT_SEED = 42
# Fixed default so two runs on different days still produce exactly the same data.
DEFAULT_END_DATE = "2026-09-30"
DEFAULT_DUPLICATE_RATE = 0.05


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the F5 reviews database.")
    parser.add_argument("--mode", choices=MODES, default=os.getenv("SEED_MODE", "dev"))
    parser.add_argument("--seed", type=int, default=int(os.getenv("SEED_VALUE", DEFAULT_SEED)))
    parser.add_argument(
        "--end-date",
        type=date.fromisoformat,
        default=date.fromisoformat(os.getenv("SEED_END_DATE", DEFAULT_END_DATE)),
    )
    parser.add_argument(
        "--start-date",
        type=date.fromisoformat,
        default=os.getenv("SEED_START_DATE"),
        help="Defaults to end-date minus the number of days of the mode",
    )
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
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
    return SeedConfig(
        seed=args.seed,
        start_date=start,
        end_date=end,
        reviews_per_day=int(args.reviews_per_day or mode["reviews_per_day"]),
        duplicate_rate=args.duplicate_rate,
    )


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    config = build_config(args)

    # Imported here so --help works without a database configured.
    from src.seed.runner import run_seed
    from src.shared.database.session_db import engine

    logging.getLogger("seed").info("Seeding with %s (mode=%s)", config, args.mode)
    run_seed(engine, config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
