"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   SharedDataTemplate Model
"""

from .model import Model


class SharedDataTemplate(Model):
    """ SharedDataTemplate Model """

    # default __init__

    def add_field(self, key: str, ftype: str) -> None:
        """ Adds a field of type `ftype` """
        # it creates if not existent
        self.Field[key] = {'Type': ftype}

    def remove_field(self, key: str) -> None:
        """ Remove a field """
        try:
            self.Field.delete(key)
        except ValueError:  # key not found
            # logger.error
            pass

    def get_fields_list(self):
        """ List of field names """
        return list(self.Fields)

Model.register_model_class('SharedDataTemplate', SharedDataTemplate)
