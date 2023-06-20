"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva  (manuel.silva@mov.ai) - 2020
"""

import ast
import re
import os
from movai_core_shared.logger import Log
from dal.models.scopestree import scopes
from dal.models.var import Var
from dal.movaidb import MovaiDB
from ..new_models import Configuration


class ParamParser:
    """
    Parser for the node instance, container and flow parameters
    Supports configuration. parameters, var, flow and env variables
    """

    logger = Log.get_logger("ParamParser.mov.ai")

    __REGEX__ = r"\$\((param|config|var|flow)[^$)]+\)"

    def __init__(self, flow):
        self.mapping = {
            "config": self.eval_config,
            "param": self.eval_param,
            "var": self.eval_var,
            "flow": self.eval_flow,
        }
        self.flow = flow  # instance of a flow

        # context is required in order to the parse the expression $(flow varA) correctly
        # context is used to go up from a subflow instance to the main flow
        self.context = None

    def parse(
        self,
        key: str,
        expression: str,
        node_name: str = None,
        instance: any = None,
        context: str = None,
    ) -> any:
        """
        Returns the parameter value. If the value is a valid expression, it is evaluated.

        Parameters:
            key (str): name of the requested parameter
            expression (str): the expression to be evaluated
                format: $(context reference)
            node_name (str): the node name
            instance (NodeInst || Container): an instance
            context (str): the context of the evaluation (main flow)

        Returns:
            output (str): the parameter value after evaluation
        """

        # support env vars
        expression = os.path.expandvars(expression)

        # assign a different context if needed
        self.context = context or self.flow.ref

        while 1:
            temp_param = expression

            expression = re.sub(
                self.__REGEX__,
                lambda m: self.eval_reference(key, m.group(), instance, node_name),
                expression,
            )

            if expression == temp_param:
                try:
                    # try to eval str as python literal ex.: "[1,2,3,4]"
                    return ast.literal_eval(expression)

                except (ValueError, SyntaxError):
                    return expression

        return expression

    def eval_reference(
        self, key: str, expression: str, instance: any, node_name: str
    ) -> str:
        """
        Calls a specific function to evaluate the expression

        Parameters:
            key (str): name of the requested parameter
            expression (str): the expression to be evaluated
                format: $(context reference)
            instance (NodeInst || Container): an instance
            node_name (str): node instance name (may be in the context of a subflow)


        Returns:
            output (str): the parameter value after evaluation
        """
        output = expression

        try:
            # $(<context> <parameter reference>)
            # ex.: $(flow var_A)
            pattern = re.compile(
                rf"\$\(({'|'.join(self.mapping.keys())})\s+([\w\.-]+)\)"
            )
            result = pattern.search(expression)
            if result is None:
                raise ValueError(f'Invalid expression "{expression}"')

            if result is None:
                raise ValueError(f"Invalid expression, {expression}")
            # get the function to call from the mapping dict
            func = self.mapping.get(result.group(1))

            # call
            output = func(result.group(2), expression, instance, node_name)

        except ValueError as error:
            extra_info = f'in flow "{self.flow.ref}"'

            if self.context != self.flow.ref:
                extra_info = f'in subflow "{self.context}" in the context of the flow "{self.flow.ref}"'

            info = (
                f'Error evaluating "{key}" with value "{expression}"'
                f' of node "{instance.name}" {extra_info}'
            )

            msg = f"{info}; {error}"

            self.logger.error(msg)

        return str(output)

    def eval_config(self, _config: str, *__):
        """
        Returns the config expression evaluated
            $(<contex> <configuration name>.<parameter reference>)
            ex.: $(config name.var1.var2)

        Parameters:
            _config (str): <configuration name>.<parameter reference>

        Returns:
            output (any): the expression evaluated
        """

        _config_name, _config_param = _config.split(".", 1)
        obj = Configuration(_config_name)

        output = obj.get_param(_config_param)

        return output

    def eval_param(
        self, param_name: str, default: str, instance: any, node_name: str
    ) -> any:
        """
        Returns the param expression evaluated or default
            ex.: $(param name)

        Parameters:
            param_name (str): reference to a parameter
            default (str): default value with parsing
            instance (NodeInst || Container): an instance
            node_name (str): node instance name (may be in the context of a subflow)

        Returns:
            output (any): the value of the parameter or the default
        """

        output = instance.get_param(param_name, node_name, self.context) or default

        return output

    def eval_var(self, reference: str, *__) -> any:
        """
        Returns the var expression evaluated
            ex.: $(var robot.name)

            Parameters:
                reference (str): reference to
                 a parameter  <fleet or robot>.<parameter reference>

            Returns:
                output (any): the expression evaluated
        """

        context, param_name, *__ = reference.split(".")
        robot_name = ""
        if context == "fleet":
            robot_name = list(MovaiDB("local").get({"Robot": "*"})["Robot"].keys())[0]

        output = Var(context, robot_name).get(param_name)

        if not output:
            raise ValueError(f'"{param_name}" does not exist in Var "{context}"')

        return output

    def eval_flow(self, param_name, default, instance, node_name) -> any:
        """
        Returns the flow expression evaluated
            ex.: $(flow myvar)

            Parameters:
                param_name (str): reference to a parameter
                default (str): default value with parsing
                instance (NodeInst || Container): an instance
                node_name (str): node instance name (may be in the context of a subflow)

            Returns:
                output (any): the expression evaluated
        """

        node_name_arr = node_name.split("__")

        value = instance.flow.get_param(param_name, self.context)
        if value is None:
            value = default

        if len(node_name_arr) > 1:
            # instance is not in the main flow

            # not using istance bc import
            if type(instance).__name__ in ["NodeInst", "Container"]:
                ctr_arr = node_name_arr[:-1]

                if ctr_arr:
                    # get the name of the container
                    _name = "__".join(ctr_arr)

                    # get the container instance
                    ctr_instance = self.flow.get_container(_name, self.context)

                    # get the parameter value
                    ctr_value = ctr_instance.get_param(param_name, _name, self.context)

                    value = value if ctr_value is None else ctr_value

            else:
                msg = f'Instance type "{type(instance).__name__}" not supported'
                raise ValueError(msg)

        return value


def get_string_from_template(template: str, task_entry: object) -> str:
    """Applies a task entry into a template"""

    if not isinstance(template, str):
        return ""

    def _replacer(match):
        try:
            template, enum = match[1].split(".")
            return str(
                scopes()
                .SharedDataEntry[task_entry.SharedData[template].ID]
                .Field[enum]
                .Value
            )
        except Exception:  # pylint: disable=broad-except
            # ValueError from split/unpack
            # or another from somewhere
            # return the original value
            return match[0]

    return re.sub(r"\{(.*?)\}", _replacer, template)
