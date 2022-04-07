"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   SharedDataEntry Model
"""

from typing import Any
from dal.scopes import scopes
from .model import Model
from .shareddatatemplate import SharedDataTemplate


class SharedDataEntry(Model):
    """ SharedDataEntry Model """

    __RELATIONS__ = {
        "schemas/1.0/SharedDataEntry/TemplateID": {
            "schema_version": "1.0",
            "scope": "SharedDataTemplate"
        }
    }

    # TODO set TemplateID on creation
    # default __init__

    @property
    def template(self) -> SharedDataTemplate:
        """ Get this' shared data template """
        return scopes.from_path(self.TemplateID, scope="SharedDataTemplate")

    def set_field_value(self, key: str, value: Any) -> None:
        """ Set the field's value """
        try:
            self.Field[key].Value = value
        except KeyError:
            pass    # logger.error()

    def get_field_value(self, key: str) -> Any:
        """ Get the field's value """

        try:
            return self.Field[key].Value
        except KeyError:
            return None
        # logger.error()

Model.register_model_class('SharedDataEntry', SharedDataEntry)
