import factory
from faker import Faker

from app.models import Payload, TransformerCache

fake = Faker()


class PayloadFactory(factory.Factory):
    """Generates fake data for the Payload model."""

    class Meta:
        model = Payload

    id = factory.LazyFunction(lambda: str(fake.uuid4()))
    input_hash = factory.LazyFunction(fake.sha256)
    result_text = factory.LazyAttribute(lambda _: f"{fake.word().upper()}, {fake.word().upper()}")


class TransformerCacheFactory(factory.Factory):
    """Generates fake data for the transformation cache."""

    class Meta:
        model = TransformerCache

    original_text = factory.LazyFunction(fake.word)
    transformed_text = factory.LazyAttribute(lambda obj: obj.original_text.upper())
