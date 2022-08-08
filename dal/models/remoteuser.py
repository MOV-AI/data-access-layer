from dal.models.model import Model
from dal.models.baseuser import BaseUser


class RemoteUser(BaseUser):
    pass


Model.register_model_class("RemoteUser", RemoteUser)
