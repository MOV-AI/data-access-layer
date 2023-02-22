import pydantic
from .general_data import GeneralMessage

class AlertData(pydantic.BaseModel):
    name: str
    info: str
    action: str
    callback: str
    status: str

class AlertMessage(GeneralMessage):
    req_data: AlertData
