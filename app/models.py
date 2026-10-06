import uuid

from sqlalchemy import Column, Integer, String

from app.database import Base


class TransformerCache(Base):
    """Stores the cached results of the simulated transformer function."""

    __tablename__ = "transformer_cache"

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(String, unique=True, index=True, nullable=False)
    transformed_text = Column(String, nullable=False)


class Payload(Base):
    """Stores the generated payload results to reuse identifiers for identical requests."""

    __tablename__ = "payloads"

    # UUID as a string to serve as the unique payload identifier
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    # A hash of the input data allows us to quickly check if we already processed this exact input
    input_hash = Column(String, unique=True, index=True, nullable=False)
    result_text = Column(String, nullable=False)
