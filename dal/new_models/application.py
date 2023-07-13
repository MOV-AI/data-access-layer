from .base_model import MovaiBaseModel
from typing import Any


class Application(MovaiBaseModel):
    User: str
    Type: str
    Package: str
    EntryPoint: str
    Icon: str
    Configuration: str
    CustomConfiguration: str
    Callbacks: Any
