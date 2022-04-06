"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   TaskTemplate Model
"""

import re
from ..scopes import scopes
from .model import Model


class TaskTemplate(Model):
    """ TaskTemplate Model """

    __RELATIONS__ = {
        "schemas/1.0/TaskTemplate/Flow": {
            "schema_version": "1.0",
            "scope": "Flow"
        },
        "schemas/1.0/TaskTemplate/ScoringFunction": {
            "schema_version": "1.0",
            "scope": "Callback"
        },
        "schemas/1.0/TaskTemplate/GenericScoringFunction": {
            "schema_version": "1.0",
            "scope": "Callback"
        },
        "schemas/1.0/TaskTemplate/TaskFilter": {
            "schema_version": "1.0",
            "scope": "Callback"
        }
    }

    # default __init__

    def add_sdentry(self, key: str, enumerator: str):
        """ Add shared data entry and the enumerator """
        self.SharedData[key] = {'Enumerator': enumerator}

    def remove_sdentry(self, key: str):
        """ Remove shared data entry """
        self.SharedData.delete(key)

    def add_scoringfunction(self, function_name: str):
        """ Add the scoring function callback name """
        # TODO verify exists and all
        self.ScoringFunction = function_name

    def add_genericscoringfunction(self, function_name: str):
        """ Adds the generic scoring function callback name """
        self.GenericScoringFunction = function_name

    def add_taskfilter(self, function_name: str):
        """ Adds the task filter callback name """
        self.TaskFilder = function_name

    def add_flow(self, flow_name: str):
        """ Adds the flow name """
        self.Flow = flow_name

    def get_enumerators(self):
        """ return the list of all the shareddataentries with enumerators """
        return list(self.SharedData)    # just want the keys

    def verify_template(self, attributes) -> bool:
        """ a function that does things """

        for attribute in attributes:
            # will raise if different that two
            sd_temp, sd_enum = attribute.split('.')

            if sd_temp not in self.SharedData:
                raise ValueError(f"SD {sd_temp} is not associated with this TaskTemplate")

            sd = scopes.from_path(sd_temp, scope='SharedDataTemplate')
            if sd_enum not in sd.Field:
                raise ValueError(f"SD {sd_temp} has no {sd_enum} field")

        # if all went fine
        return True

    def add_description_template(self, template: str) -> bool:
        """ verify and add description template """
        try:
            # will blow up if False
            self.verify_template(
                re.findall(r"\{(.*?)\}", template)
            )
            self.Description_Template = template
            return True
        except ValueError:
            return False

    def add_label_template(self, template: str) -> bool:
        """ verify and add label template """
        try:
            # will blow up if False
            self.verify_template(
                re.findall(r"\{(.*?)\}", template)
            )
            self.Label_Template = template
            return True
        except ValueError:
            return False

Model.register_model_class("TaskTemplate", TaskTemplate)
