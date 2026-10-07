from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Base
from app.schemas import PayloadCreateRequest, PayloadCreateResponse, PayloadReadResponse
from app.services import get_payload_by_id, process_payload


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


@app.post(
    "/payload",
    response_model=PayloadCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payload(request: PayloadCreateRequest, db: Annotated[Session, Depends(get_db)]):
    """
    Accepts two lists of strings, transforms them, interleaves the results, and caches the payload.
    """
    logger.info("Received request to generate payload.")
    payload_id = process_payload(db=db, request=request)

    return PayloadCreateResponse(message="Payload successfully generated.", id=payload_id)


@app.get(
    "/payload/{payload_id}",
    response_model=PayloadReadResponse,
    status_code=status.HTTP_200_OK,
)
def read_payload(payload_id: str, db: Annotated[Session, Depends(get_db)]):
    """Retrieves a previously generated payload by its ID."""
    logger.info(f"Fetching payload with ID: {payload_id}")
    payload = get_payload_by_id(db=db, payload_id=payload_id)

    if not payload:
        logger.warning(f"Payload not found: {payload_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payload not found.")

    return PayloadReadResponse(output=payload.result_text)
