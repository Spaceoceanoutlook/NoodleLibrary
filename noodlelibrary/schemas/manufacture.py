from pydantic import BaseModel, ConfigDict, Field


class ManufactureBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
