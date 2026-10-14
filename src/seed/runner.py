import logging
from dataclasses import dataclass

from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.engine import Engine

from src.models.review_model import Review
from src.seed.generator import SeedConfig, generate

logger = logging.getLogger("seed")

CHUNK_SIZE = 1_000


@dataclass
class SeedResult:
    generated: int = 0
    inserted: int = 0

    @property
    def skipped(self) -> int:
        return self.generated - self.inserted


def _insert_ignoring_duplicates(engine: Engine):
    """INSERT ... ON CONFLICT (platform, external_id) DO NOTHING for the current dialect."""
    dialect = engine.dialect.name
    if dialect == "postgresql":
        insert = postgresql.insert
    elif dialect == "sqlite":
        insert = sqlite.insert
    else:  # pragma: no cover - only Postgres (local/RDS) and SQLite (tests) are supported
        raise RuntimeError(f"Unsupported database dialect: {dialect}")

    def build(rows: list[dict]):
        return (
            insert(Review.__table__)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["platform", "external_id"])
            # rowcount is unreliable for multi-row inserts; count the ids actually inserted
            .returning(Review.__table__.c.id)
        )

    return build


def run_seed(engine: Engine, config: SeedConfig, dry_run: bool = False) -> SeedResult:
    result = SeedResult()
    build_insert = _insert_ignoring_duplicates(engine)
    buffer: list[dict] = []

    def flush() -> None:
        if not buffer:
            return
        if not dry_run:
            with engine.begin() as connection:
                result.inserted += len(connection.execute(build_insert(buffer)).all())
        buffer.clear()

    for day_rows in generate(config):
        result.generated += len(day_rows)
        buffer.extend(day_rows)
        if len(buffer) >= CHUNK_SIZE:
            flush()
    flush()

    logger.info(
        "Seed finished: generated=%s inserted=%s skipped(existing)=%s",
        result.generated,
        result.inserted,
        result.skipped,
    )
    return result
