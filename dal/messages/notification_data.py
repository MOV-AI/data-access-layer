from .email_data import EmailData
from .sms_data import SMSData
from .user_data import UserData


class NotificationDataFactory:
    _data_classes = {"smtp": EmailData, "sms": SMSData, "user": UserData}

    @classmethod
    def create(cls, notification_type: str, notification_data: dict):
        """create an Object according to the type of the notification

        Args:
            notification_type (str): the notificaiton type.
            notification_data (dict): the notification data.

        Returns:
            Obj: dataclass like obj representing the notification data
        """
        return cls._data_classes[notification_type](**notification_data)
