import logging
import time

from fastapi import FastAPI, Request

from src.api.errors import register_error_handlers
from src.api.routers import health, hotels, reviews
from src.core.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("api_reviews")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Simulated F5 source for HospedaPlus Revenue: guest reviews from several "
        "platforms (Booking, Google, Tripadvisor, Expedia) in Spanish, English and "
        "Portuguese, exposed as a paginated REST API."
    ),
)

register_error_handlers(app)
app.include_router(health.router)
app.include_router(hotels.router)
app.include_router(reviews.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    if request.url.path != "/health":  # keep ALB health checks out of the logs
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
    return response
