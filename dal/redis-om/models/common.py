from redis_om import HashModel
from typing import Optional


class Arg(HashModel):
    Description: Optional[str] = None
    Value: object
    Type: Optional[str] = None
