from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.database import engine
from app.models import Base
from app.routes import router as payload_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events for the FastAPI application."""
    logger.info("Starting application: Creating database tables.")
    Base.metadata.create_all(bind=engine)

    yield  # Application is running

    logger.info("Shutting down application: Disposing database engine.")
    engine.dispose()


app = FastAPI(
    title="Caching Service",
    description="Microservice for interleaving and caching string transformations.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(payload_router)
