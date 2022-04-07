"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   TaskEntry Model
"""
from dal.scopes import scopes
from dal.helpers import get_string_from_template
from .tasktemplate import TaskTemplate
from .model import Model


class TaskEntry(Model):
    """ TaskEntry Model """

    __RELATIONS__ = {
        "schemas/1.0/TaskEntry/TemplateID": {
            "schema_version": "1.0",
            "scope": "TaskTemplate"
        },
        "schemas/1.0/TaskEntry/SharedData/ID": {
            "schema_version": "1.0",
            "scope": "SharedDataEntry"
        }
    }

    # TODO set TemplateID on creation
    # default __init__

    @property
    def template(self) -> TaskTemplate:
        """ Get template instance """
        return scopes().from_path(self.TemplateID, scope="TaskTemplate")

    def set_shareddata_id(self, key: str, sd_id: str) -> None:
        """ Set shared data's ID value """
        if key in self.template.SharedData: # .keys()
            self.SharedData[key].ID = sd_id

    def get_shareddata_entries(self):
        """ Get the list of SharedDataEntries """
        return [
            scopes().from_path(sd.ID, scope="SharedDataEntry")
            for sd in self.SharedData.items()
        ]

    @staticmethod
    def get_string_from_template(template: str, _: dict, te_name: str) -> str:
        """ Decode the template description and label """
        # use the one from parsers
        return get_string_from_template(
            template, scopes.from_path(te_name, scope='TaskEntry')
        )

Model.register_model_class("TaskEntry", TaskEntry)
