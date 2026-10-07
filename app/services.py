import hashlib
import json

from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payload, TransformerCache
from app.schemas import PayloadCreateRequest


class PayloadService:
    """Service class encapsulating business logic for payload processing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _simulate_external_transformer(self, text: str) -> str:
        """
        Simulates an external service call.
        For this task, we will simply convert the string to uppercase.
        """
        return text.upper()

    def _generate_input_hash(self, list_1: list[str], list_2: list[str]) -> str:
        """
        Generates a deterministic SHA-256 hash for the input lists.
        This allows us to quickly identify identical past requests.
        """
        data = json.dumps({"list_1": list_1, "list_2": list_2}, sort_keys=True)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    async def process_payload(self, request: PayloadCreateRequest) -> str:
        """Processes the incoming payload request optimally using bulk DB operations."""
        input_hash = self._generate_input_hash(list_1=request.list_1, list_2=request.list_2)

        # Async query for existing payload
        result = await self.db.execute(select(Payload).filter(Payload.input_hash == input_hash))
        existing_payload = result.scalars().first()

        if existing_payload:
            logger.info(f"Payload cache hit. Reusing ID: {existing_payload.id}")
            return existing_payload.id

        # Extract all unique strings to minimize external calls and DB queries
        unique_strings = set(request.list_1 + request.list_2)

        # Async bulk fetch from cache
        cache_result = await self.db.execute(
            select(TransformerCache).filter(TransformerCache.original_text.in_(unique_strings))
        )
        cached_records = cache_result.scalars().all()

        # Map original text to its transformed version for O(1) lookup
        transform_map = {record.original_text: record.transformed_text for record in cached_records}

        # Find missing strings, call external service, and prepare bulk insert
        new_cache_entries = []
        for text in unique_strings:
            if text not in transform_map:
                transformed_text = self._simulate_external_transformer(text)
                transform_map[text] = transformed_text
                new_cache_entries.append(
                    TransformerCache(original_text=text, transformed_text=transformed_text)
                )

        # Bulk insert new cache entries to avoid DB locks in a loop
        if new_cache_entries:
            logger.debug(
                f"Calling external transformer for {len(new_cache_entries)} new unique words."
            )
            self.db.add_all(new_cache_entries)

            # Handle race condition: another concurrent request might have just cached these words
            try:
                await self.db.commit()
            except IntegrityError:
                await self.db.rollback()
                logger.warning(
                    "Cache race condition detected: "
                    "Some words were already saved by another transaction. "
                    "Falling back to in-memory cache."
                )

        # Interleave the transformed strings
        result_parts = []
        for s1, s2 in zip(request.list_1, request.list_2, strict=True):
            result_parts.append(transform_map[s1])
            result_parts.append(transform_map[s2])

        result_text = ", ".join(result_parts)

        # Store the new payload result
        new_payload = Payload(input_hash=input_hash, result_text=result_text)
        self.db.add(new_payload)

        # Handle race condition: another concurrent request might have just saved this exact payload
        try:
            await self.db.commit()
            await self.db.refresh(new_payload)
            logger.info(f"Generated and cached new payload: {new_payload.id}")
        except IntegrityError:
            await self.db.rollback()
            result = await self.db.execute(select(Payload).filter(Payload.input_hash == input_hash))
            existing_payload = result.scalars().first()
            logger.warning(
                "Payload race condition detected: "
                f"Returning concurrently saved ID: {existing_payload.id}"
            )
            return existing_payload.id

        return new_payload.id

    async def get_payload_by_id(self, payload_id: str) -> Payload | None:
        """Retrieves a generated payload by its unique id."""
        result = await self.db.execute(select(Payload).filter(Payload.id == payload_id))
        return result.scalars().first()
