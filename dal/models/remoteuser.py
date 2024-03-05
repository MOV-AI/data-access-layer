"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Erez Zomer  (erez@mov.ai) - 2022
"""
from .model import Model
from .baseuser import BaseUser


class RemoteUser(BaseUser):
    """This class represents the remote user object as record in the DB."""

    pass


Model.register_model_class("RemoteUser", RemoteUser)
