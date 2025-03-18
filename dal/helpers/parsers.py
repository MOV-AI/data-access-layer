import ast
from functools import partial
import os
import re
import types
from typing import Protocol, Optional, Any, cast

from lark import Lark, Transformer
import lark.exceptions

from movai_core_shared.logger import Log
from dal.models.scopestree import scopes
from dal.models.var import Var
from dal.movaidb import MovaiDB

grammar = r"""
    start: expr

    expr: command_call
        | VAL

    command_call: "$(" IDENTIFIER expr* ")"  // First token is the command name

    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/  // Command or variable names (e.g., flow, param)
    VAL: /[a-zA-Z_][a-zA-Z0-9_.]*/     // Simple values like debug treated as strings

    %ignore " "  // Ignore spaces
"""

logger = Log.get_logger("ParamParser.mov.ai")


class ObjectWithName(Protocol):
    @property
    def name(self) -> str:
        ...


class PythonASTTransformer(Transformer):
    """ Transform the Parameter configuration syntax into Python AST

    We essentially transform an expression like:

        $(config $(flow debug).var1)

    into the equivalent Python code:

        config(flow("debug").var1)

    Then, we tell the Python interpreter to execute that code.

    (Note: we don't actually generate Python code, we generate a
    Python Abstract Syntax Tree (AST) """

    def expr(self, items):
        return items[0]  # Return the expression

    def command_call(self, items):
        # The first item is the command name (treated as a Name)
        command = ast.Name(id=items[0].value, ctx=ast.Load(), lineno=items[0].line, col_offset=items[0].column)
        args = items[1:]

        # Create the Call AST node, adding a lineno and col_offset from the first token (command)
        return ast.Call(
            func=command,
            args=args,  # Arguments (simple values)
            keywords=[],
            lineno=command.lineno,
            col_offset=command.col_offset
        )

    def VAL(self, token):
        # Return the value as a Constant
        return ast.Constant(value=token.value, kind=None, lineno=token.line, col_offset=token.column)


_parser = Lark(grammar, start="expr", parser="lalr", transformer=PythonASTTransformer())


class ParamParser:
    def __init__(self, flow):
        self.flow = flow

    def parse(
        self,
        key: str,
        expression: str,
        node_name: str,
        instance: ObjectWithName,
        context: Optional[str] = None,
    ) -> Any:

        # Support env vars
        expression_ = os.path.expandvars(expression)
        context = context or self.flow.ref

        # The transformer will always return an AST expression
        try:
            parsed_ast = cast(ast.expr, _parser.parse(expression_))
        except lark.exceptions.LarkError as error:
            self._log_expression_error(key, expression, instance, context, error)
            return None

        # Define the available commands
        # we use partial to transparently pass some extra arguments
        eval_context = {
            "param": partial(self.eval_param, instance=instance, node_name=node_name, context=context),
            "config": self.eval_config,
            "var": self.eval_var,
            "flow": partial(self.eval_flow, instance=instance, node_name=node_name, context=context),
        }

        # Validate and compile the Parameter expression
        try:
            code_obj = compile(ast.Expression(body=parsed_ast), expression, "eval")
        except TypeError as error:
            self._log_expression_error(key, expression, instance, context, error)
        else:
            return eval(code_obj, eval_context)

    def _log_expression_error(self, key, expression, instance, context, error):
        extra_info = f'in flow "{self.flow.ref}"'

        if context != self.flow.ref:
            extra_info = (
                f'in subflow "{context}" in the context of the flow "{self.flow.ref}"'
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

        logger.error(msg)

    def eval_config(self, _config: str):
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
            obj = scopes.from_path(_config_name, scope="Configuration")

        except KeyError as exc:
            raise ValueError(f"Configuration {_config_name} does not exist") from exc

        output = obj.get_param(_config_param)

        return output

    def eval_param(self, param_name: str, instance, node_name, context) -> Any:
        """
        Returns the param expression evaluated or default
            ex.: $(param name)

        Parameters:
            param_name (str): reference to a parameter
            instance (NodeInst || Container): an instance
            node_name (str): node instance name (may be in the context of a subflow)

        Returns:
            output (any): the value of the parameter or the default
        """

        return instance.get_param(param_name, node_name, context)

    def eval_var(self, reference: str) -> Any:
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

    def eval_flow(self, param_name, instance, node_name, context) -> Any:
        """
        Returns the flow expression evaluated
            ex.: $(flow myvar)

            Parameters:
                param_name (str): reference to a parameter
                instance (NodeInst || Container): an instance
                node_name (str): node instance name (may be in the context of a subflow)

            Returns:
                output (any): the expression evaluated
        """

        node_name_arr = node_name.split("__")
        # Check if this is the main flow or a subflow
        is_subflow = len(node_name_arr) > 1

        if is_subflow:
            # instance is not in the main flow

            # not using istance bc import
            if type(instance).__name__ in ["NodeInst", "Container"]:
                ctr_arr = node_name_arr[:-1]

                if ctr_arr:
                    # get the name of the container
                    _name = "__".join(ctr_arr)

                    # get the container instance
                    ctr_instance = self.flow.get_container(_name, context)

                    # get the instance parameter value
                    # if there is no instance param, set to default
                    ctr_expr = ctr_instance.get_param_expr(
                        param_name, _name, context
                    )

                    if ctr_expr:
                        return self.parse(param_name, ctr_expr, _name, ctr_instance, context)

            else:
                msg = f'Instance type "{type(instance).__name__}" not supported'
                raise ValueError(msg)

        # No param in top flow, read from current flow
        return instance.flow.get_param(param_name, context, is_subflow=is_subflow)


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
