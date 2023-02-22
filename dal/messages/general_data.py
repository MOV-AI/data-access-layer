import pydantic
from typing import Optional

class RobotInfo(pydantic.BaseModel):
    robot_id: str
    robot_name: str
    service_name: str
    fleet_name: str


class GeneralMessage(pydantic.BaseModel):
    robot_info: RobotInfo
    created: str
    req_type: str
    measurement: str
    response_required: Optional[bool]
