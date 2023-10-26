from .base import MovaiBaseModel
from typing import List, Any
from pydantic import Field


class Application(MovaiBaseModel):
    User: str = ""
    Type: str = ""
    Package: str = ""
    EntryPoint: str = ""
    Icon: str = ""
    Configuration: str = ""
    CustomConfiguration: str = ""
    Callbacks: List[Any] = Field(default_factory=list)
