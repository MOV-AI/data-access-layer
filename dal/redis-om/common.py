from redis_om import EmbeddedJsonModel, Field
from typing import Optional


class LastUpdate(EmbeddedJsonModel):
    date: str
    user: str = Field(index=True)


class Arg(EmbeddedJsonModel):
    Description: Optional[str] = None
    Value: object
    Type: Optional[str] = None
