from typing import Optional, Dict, List, Any, Union
from pydantic import constr, BaseModel, Field
from common import Arg
from base import MovaiBaseModel


class DataValue(BaseModel):


class InOutValue(BaseModel):
    Transport: str
    Protocol: str
    Message: str
    Callback: str
    Parameter: hash
    LinkEnabled: bool 

class Ports(MovaiBaseModel):
    Data: DataValue =
    In: Optional[InValue] = None
    Out: Optional[OutValue] = None
