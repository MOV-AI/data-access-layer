import pydantic


class UserData(pydantic.BaseModel):
    notification_type: str = "user"
    msg: str
    robot_id: str
    robot_name: str
