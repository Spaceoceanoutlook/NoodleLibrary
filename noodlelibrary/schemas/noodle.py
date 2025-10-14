from typing import Optional

from pydantic import BaseModel, ConfigDict


class NoodleBase(BaseModel):
    title: str
    description: Optional[str] = None
    image: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
