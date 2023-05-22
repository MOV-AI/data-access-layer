import pydantic
from typing import List


class SMSData(pydantic.BaseModel):
    recipients: List[str]
    msg: str
    notification_type: str
