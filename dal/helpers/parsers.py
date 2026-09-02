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
from typing import TYPE_CHECKING, Any, Optional, Protocol, Union, cast, List, Tuple

from movai_core_shared.logger import Log
from movai_core_shared.envvars import RAISE_FLOW_VALIDATION_ERRORS
from dal.models.scopestree import scopes
from dal.models.var import Var
from dal.movaidb import MovaiDB
from dal.exceptions import (
    UndefinedFlowParameterError,
    UndefinedConfigParameterError,
    UndefinedVarParameterError,
    UndefinedParamParameterError,
)

if TYPE_CHECKING:
    from dal.models.container import Container
    from dal.models.flow import Flow
    from dal.models.nodeinst import NodeInst
    from dal.models.configuration import Configuration


class ObjectWithName(Protocol):
    @property
    def name(self) -> str:
        ...


class ParamParser:
    """
    Parser for the node instance, container and flow parameters
    Supports configuration. parameters, var, flow and env variables
    """

    logger = Log.get_logger("ParamParser.mov.ai")

    __REGEX__ = r"\$\((param|config|var|flow)[^$)]+\)"

    def __init__(self, flow: "Flow"):
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
        node_name: str,
        instance: ObjectWithName,
        context: Optional[str] = None,
    ) -> Any:
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
        self, key: str, expression: str, instance: ObjectWithName, node_name: str
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
            pattern = re.compile(rf"\$\(({'|'.join(self.mapping.keys())})\s+([\w\.-]+)\)")
            result = pattern.search(expression)

            if result is None:
                raise ValueError(f"Invalid expression, {expression}")
            # get the function to call from the mapping dict
            func = self.mapping[result.group(1)]

            # call
            output = func(result.group(2), expression, instance, node_name)

        except ValueError as error:
            extra_info = f'in flow "{self.flow.ref}"'

            if self.context != self.flow.ref:
                extra_info = (
                    f'in subflow "{self.context}" in the context of the flow "{self.flow.ref}"'
                )

            from dal.models.flow import Flow

            if isinstance(instance, Flow):
                info = (
                    f'Error evaluating "{key}" with value "{expression}"'
                    f' of flow "{self.flow.ref}"'
                )
            else:
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
        try:
            obj = cast("Configuration", scopes.from_path(_config_name, scope="Configuration"))

        except KeyError as exc:
            if RAISE_FLOW_VALIDATION_ERRORS:
                raise UndefinedConfigParameterError(
                    f"Configuration {_config_name} does not exist"
                ) from exc
            else:
                self.logger.error(
                    "VALIDATION ERRORS DISABLED: Configuration "
                    f'"{_config_name}" does not exist. Using default value.'
                )
                return None

        output = obj.get_param(_config_param)

        return output

    def eval_param(
        self,
        param_name: str,
        default: str,
        instance: Union["Flow", "NodeInst", "Container"],
        node_name: str,
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

        cls_name = type(instance).__name__
        if cls_name == "Flow":  # Flows don't have a node name
            if not instance.has_param(param_name):
                if RAISE_FLOW_VALIDATION_ERRORS:
                    raise UndefinedParamParameterError(
                        f'Parameter "{param_name}" is not defined in flow "{instance.ref}"'
                    )
                else:
                    self.logger.error(
                        "VALIDATION ERRORS DISABLED: Parameter "
                        f'"{param_name}" is not defined in flow "{instance.ref}". '
                        "Using default value."
                    )
                    return default
            instance = cast("Flow", instance)
            output = instance.get_param(param_name, self.context) or default
        elif cls_name in ["NodeInst", "Container"]:
            if not instance.has_param(param_name, node_name, self.context):
                if RAISE_FLOW_VALIDATION_ERRORS:
                    raise UndefinedParamParameterError(
                        f'Parameter "{param_name}" is not defined in '
                        f'"{node_name}" of flow "{instance.flow.ref}"'
                    )
                else:
                    self.logger.error(
                        "VALIDATION ERRORS DISABLED: Parameter "
                        f'"{param_name}" is not defined in "{node_name}" '
                        f'of flow "{instance.flow.ref}". Using default value.'
                    )
                    return default
            output = instance.get_param(param_name, node_name, self.context) or default
        else:
            raise ValueError(f'Instance type "{cls_name}" not supported')

        return output

    def eval_var(self, reference: str, *__) -> Any:
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
            if RAISE_FLOW_VALIDATION_ERRORS:
                raise UndefinedVarParameterError(
                    f'"{param_name}" does not exist in Var "{context}"'
                )
            else:
                self.logger.error(
                    "VALIDATION ERRORS DISABLED: "
                    f'"{param_name}" does not exist in Var "{context}". '
                    "Using default value."
                )
                return None

        return output

    @staticmethod
    def _has_unresolved_flow_reference(value: Any) -> bool:
        """Returns whether a parsed value still contains a flow reference."""

        return isinstance(value, str) and re.search(r"\$\(flow\s+[\w\.-]+\)", value) is not None

    def _get_parent_containers(self, node_name_arr: list) -> List[Tuple[str, "Container"]]:
        """Returns parent containers from nearest to farthest for a node path."""

        containers = []

        for index in range(len(node_name_arr) - 1, 0, -1):
            container_name = "__".join(node_name_arr[:index])
            container = self.flow.get_container(container_name, self.context)
            assert container is not None, f"Container {container_name} not found"
            containers.append((container_name, container))

        return containers

    def eval_flow(
        self,
        param_name: str,
        default: str,
        instance: Union["NodeInst", "Container"],
        node_name: str,
    ) -> any:
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
        # Check if this is the main flow or a subflow
        is_subflow = len(node_name_arr) > 1

        flow = instance.flow
        cls_name = type(instance).__name__
        flow_has_param = flow.has_param(param_name)

        # Check if the main flow has the parameter defined.
        if not flow_has_param:
            if not is_subflow or cls_name == "Container":
                # If this is the main flow and the parameter is not defined, raise an error
                # or
                # If a container tried to resolve a parameter that is not defined
                # in the main flow or itself, raise an error.
                if RAISE_FLOW_VALIDATION_ERRORS:
                    raise UndefinedFlowParameterError(
                        f'Flow parameter "{param_name}" is not defined in flow "{flow.ref}"'
                    )
                else:
                    self.logger.error(
                        "VALIDATION ERRORS DISABLED: Flow parameter "
                        f'"{param_name}" is not defined in flow "{flow.ref}". '
                        "Continuing with default value."
                    )
            value = default
        else:
            value = flow.get_param(param_name, context=self.context, is_subflow=is_subflow)

            # Use the default value if the flow parameter is None
            if value is None:
                value = default

        if is_subflow:
            # instance is not in the main flow, check parent containers for the parameter value
            if cls_name not in ["NodeInst", "Container"]:
                msg = f'Instance type "{cls_name}" not supported'
                raise ValueError(msg)

            containers = self._get_parent_containers(node_name_arr)

            if containers:
                container_name, container = containers[0]
                container_value = container.get_param(
                    param_name,
                    container_name,
                    self.context,
                    default_value=value,
                )

                # If the container has a value for the parameter, use it instead of the flow value
                # As this value is more specific to the node instance than the flow value
                value = value if container_value is None else container_value

        # If the value is None or still contains an unresolved flow reference,
        # it means the parameter is not defined in the flow or its parent container
        # so we raise an error
        if value is None or self._has_unresolved_flow_reference(value):
            if RAISE_FLOW_VALIDATION_ERRORS:
                raise UndefinedFlowParameterError(
                    f'Flow parameter "{param_name}" is not defined in flow "{flow.ref}"'
                )
            else:
                self.logger.error(
                    "VALIDATION ERRORS DISABLED: Flow parameter "
                    f'"{param_name}" is not defined in flow "{flow.ref}". '
                    "Returning unresolved value."
                )
                return value

        return value


def get_string_from_template(template: str, task_entry: object) -> str:
    """Applies a task entry into a template"""

    if not isinstance(template, str):
        return ""

    def _replacer(match):
        try:
            template, enum = match[1].split(".")
            return str(
                scopes().SharedDataEntry[task_entry.SharedData[template].ID].Field[enum].Value
            )
        except Exception:  # pylint: disable=broad-except
            # ValueError from split/unpack
            # or another from somewhere
            # return the original value
            return match[0]

    return re.sub(r"\{(.*?)\}", _replacer, template)
