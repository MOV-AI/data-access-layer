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
            raise UndefinedConfigParameterError(
                f"Configuration {_config_name} does not exist"
            ) from exc

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
                raise UndefinedParamParameterError(
                    f'Parameter "{param_name}" is not defined in flow "{instance.ref}"'
                )
            instance = cast("Flow", instance)
            output = instance.get_param(param_name, self.context) or default
        elif cls_name in ["NodeInst", "Container"]:
            if not instance.has_param(param_name, node_name, self.context):
                raise UndefinedParamParameterError(
                    f'Parameter "{param_name}" is not defined in "{node_name}" of flow "{instance.flow.ref}"'
                )
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
            raise UndefinedVarParameterError(f'"{param_name}" does not exist in Var "{context}"')

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
        value = None
        has_value = False
        containers: List[Tuple[str, "Container"]] = []
        nearest_container = None
        nearest_container_name = None

        if is_subflow and type(instance).__name__ in ["NodeInst", "Container"]:
            containers = self._get_parent_containers(node_name_arr)

        if containers:
            nearest_container_name, nearest_container = containers[0]

        direct_parent_flow = nearest_container.flow if nearest_container is not None else None

        if flow.has_param(param_name):
            value = flow.get_param(param_name, context=self.context, is_subflow=is_subflow)

            has_value = not self._has_unresolved_flow_reference(value)

        if nearest_container is not None and param_name in nearest_container.Parameter:
            value = nearest_container.get_param(param_name, nearest_container_name, self.context)
            has_value = not self._has_unresolved_flow_reference(value)

        if (
            not has_value
            and direct_parent_flow is not None
            and direct_parent_flow.has_param(param_name)
        ):
            value = direct_parent_flow.get_param(
                param_name,
                context=self.context,
                is_subflow=len(containers) > 1,
            )
            has_value = not self._has_unresolved_flow_reference(value)

        if self._has_unresolved_flow_reference(value):
            for container_name, container in containers[1:]:
                if param_name not in container.Parameter:
                    continue

                value = container.get_param(param_name, container_name, self.context)
                has_value = not self._has_unresolved_flow_reference(value)

                if has_value:
                    break

        if (
            not has_value
            and self._has_unresolved_flow_reference(value)
            and flow.has_param(param_name)
            and nearest_container is not None
        ):
            value = self.parse(
                param_name,
                value,
                nearest_container_name,
                nearest_container,
                self.context,
            )
            has_value = not self._has_unresolved_flow_reference(value)

        if not has_value:
            raise UndefinedFlowParameterError(
                f'Flow parameter "{param_name}" is not defined in flow "{flow.ref}"'
            )

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
