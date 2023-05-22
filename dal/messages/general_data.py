from pydantic import BaseModel


class RobotInfo(BaseModel):
    """
    a base dataclass based on pydantic basemodel in order to support
    validation and check for missing fields or wrong values.
    """

    fleet: str
    robot: str
    service: str
    id: str

    def __str__(self) -> str:
        text = f"""
            fleet: {self.fleet}
            robot: {self.robot}
            service: {self.service}
            id: {self.id}"""
        return text


class Request(BaseModel):
    req_type: str
    created: int
    response_required: bool
    robot_info: RobotInfo

    def __str__(self):
        text = f"""
        ===========================================================================================
        req_type: {self.req_type}
        response_required: {self.response_required}
        robot_info: {self.robot_info.__str__()}
        created: {self.created}
        ==========================================================================================="""
        return text
