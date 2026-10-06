from pydantic import BaseModel, Field, model_validator


class PayloadCreateRequest(BaseModel):
    """Schema for the incoming POST request payload."""

    list_1: list[str] = Field(..., description="First list of strings")
    list_2: list[str] = Field(..., description="Second list of strings")

    @model_validator(mode="after")
    def check_lengths(self) -> "PayloadCreateRequest":
        """Ensures both lists have the exact same length as required."""
        if len(self.list_1) != len(self.list_2):
            raise ValueError("list_1 and list_2 must have the same length.")
        return self


class PayloadCreateResponse(BaseModel):
    """Schema for the POST response containing the payload ID and confirmation message."""

    id: str
    message: str


class PayloadReadResponse(BaseModel):
    """Schema for the GET response containing the final result."""

    output: str
