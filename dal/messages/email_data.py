import pydantic
from re import search
from typing import List, Optional
from movai_core_shared.envvars import FLEET_NAME, DEVICE_NAME
from movai_core_shared.consts import NOTIFICATIONS_HANDLER_MSG_TYPE
from movai_core_shared.logger import Log


EMAIL_REGEX = r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"
logger = Log.get_logger(NOTIFICATIONS_HANDLER_MSG_TYPE)


class EmailData(pydantic.BaseModel):
    """
    a base dataclass based on pydantic basemodel in order to support
    validation and check for missing fields or wrong values.
    """

    recipients: List[str]
    notification_type: str = "smtp"
    subject: Optional[str]
    body: str
    attachment_data: Optional[str]
    sender: str = f"{DEVICE_NAME} {FLEET_NAME}"

    @pydantic.validator("notification_type")
    @classmethod
    def notification_type_valid(cls, value):
        if value.lower() != "smtp":
            raise ValueError("notification_type must be smtp")
        return value

    @pydantic.validator("recipients")
    @classmethod
    def recipients_valid(cls, value):
        valid = []
        for email in value:
            if not search(EMAIL_REGEX, email):
                logger.warning(f"email {email} is not a valid email address")
            else:
                valid.append(email)
        if not valid:
            raise ValueError("no valid Email Address provided for email notification")

        return valid

    class Config:
        """Pydantic config class"""

        allow_mutation = False  # make object immutable
