from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PayloadCreateRequest, PayloadCreateResponse, PayloadReadResponse
from app.services import PayloadService

router = APIRouter()


@router.post(
    "/payload",
    response_model=PayloadCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payload(request: PayloadCreateRequest, db: Annotated[Session, Depends(get_db)]):
    """
    Accepts two lists of strings, transforms them, interleaves the results, and caches the payload.
    """
    logger.info("Received request to generate payload.")

    service = PayloadService(db=db)
    payload_id = service.process_payload(request=request)

    return PayloadCreateResponse(message="Payload successfully generated.", id=payload_id)


@router.get(
    "/payload/{payload_id}",
    response_model=PayloadReadResponse,
    status_code=status.HTTP_200_OK,
)
def read_payload(payload_id: str, db: Annotated[Session, Depends(get_db)]):
    """Retrieves a previously generated payload by its ID."""
    logger.info(f"Fetching payload with ID: {payload_id}")

    service = PayloadService(db=db)
    payload = service.get_payload_by_id(db=db, payload_id=payload_id)

    if not payload:
        logger.warning(f"Payload not found: {payload_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payload not found.")

    return PayloadReadResponse(output=payload.result_text)
