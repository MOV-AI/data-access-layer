from re import match
from typing import Optional, Dict, Any
from typing_extensions import Annotated

from pydantic import StringConstraints, ConfigDict, BaseModel, Field, field_validator

from dal.new_models.base_model.common import Arg
from dal.new_models.node import Node
from dal.helpers.parsers import ParamParser


ValidName = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+$")]
PARAMETER_REGEX = r"^(/?[a-zA-Z0-9_@]+)+$"


class CmdLineValue(BaseModel):
    Value: Any = None


class EnvVarValue(BaseModel):
    Value: Any = None


class NodeInst(BaseModel):
    NodeLabel: Optional[ValidName] = None
    Parameter: Optional[Dict[str, Arg]] = Field(default_factory=dict)
    Template: Optional[ValidName] = None
    CmdLine: Optional[
        Dict[Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+$")], CmdLineValue]
    ] = Field(default_factory=dict)
    EnvVar: Optional[
        Dict[Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+$")], EnvVarValue]
    ] = Field(default_factory=dict)
    NodeLayers: Optional[Any] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Launch = None
        self.Dummy = None
        self.Remappable = None
        self.Persistent = None
        self._flow_ref = None
        self._parser = None

    model_config = ConfigDict(
        exclude={
            "Launch",
            "Dummy",
            "Remappable",
            "_parser",
        },
        extra="allow",
        arbitrary_types_allowed=True,
    )

    def model_dump(
        self,
        *,
        include=None,
        exclude=None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,
    ):
        dic = super().model_dump(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        dic.pop("_parser", None)
        dic.pop("_flow_ref", None)
        return dic

    @field_validator("Parameter", mode="before")
    def validate_regex(cls, value):
        if isinstance(value, dict):
            for key in value:
                if not match(PARAMETER_REGEX, key):
                    raise ValueError(
                        f"Field 'Parameter' with value '{key}' does not match the required pattern '{PARAMETER_REGEX}'."
                    )
        return value

    @property
    def node_template(self) -> Node:
        """
        return the current template for this node
        instance
        """
        return Node(self.Template)

    @property
    def flow(self) -> BaseModel:
        """Returns the flow (Flow)"""
        return self._parser.flow

    @property
    def type(self) -> str:
        """Returns the type of the node"""
        return self.node_template.Type

    @property
    def parser(self) -> ParamParser:
        """Get the parser from the parent (GParser)"""
        return self._parser

    @property
    def namespace(self) -> str:
        """Returns the value from the parameter _namespace"""
        return self.get_param("_namespace") or ""

    @property
    def is_nodelet(self) -> bool:
        """Returns True if the node is of type Nodelet"""
        return self.node_template.is_nodelet

    @property
    def is_state(self) -> bool:
        """Returns True if the node is of type state"""
        return self.node_template.is_state

    @property
    def is_plugin(self) -> bool:
        """Returns True if the node is of type plugin"""
        return self.node_template.is_plugin

    @property
    def is_remappable(self) -> bool:
        """Returns True if the ports are allowed to remap"""
        # get the value from the node template
        temp = self.node_template.is_remappable

        # get the value from the property Remappable
        prop = temp if self.Remappable in [None, ""] else self.Remappable
        # prop = True

        # get the value from the parameter _remappable
        # parameter takes precedence
        param = self.get_param("_remappable")

        return prop if param in [None, ""] else param

    @property
    def is_node_to_launch(self) -> bool:
        """Returns True if it should be launched"""
        # already been calculated
        if isinstance(self.Launch, tuple):
            cmd, res = self.Launch
            if cmd == "override" and isinstance(res, bool):
                return res
        # get the value from the node template
        temp = self.node_template.is_node_to_launch

        # get the value from the property Launch
        prop = temp if self.Launch in [None, ""] else self.Launch
        # prop = True

        # get the value from the parameter _launch
        # parameter takes precedence
        # Todo: remove duplication and only use "Launch" and remove "_launch"
        #       the next line is missing the context, and it can't passed with property
        #       neet to fix this garbage
        param = self.get_param("_launch")

        return prop if param in [None, ""] else param

    @property
    def is_persistent(self) -> bool:
        """Returns True if it persists on state transitions"""
        # get the value from the node template
        temp = self.node_template.is_persistent

        # get the value from the property Persistent
        prop = temp if self.Persistent in [None, ""] else self.Persistent

        # return prop if param in [None, ""] else param
        return prop

    @property
    def is_dummy(self) -> bool:
        """Returns True if the node is configured as Dummy"""
        if self.Dummy not in [None, ""]:
            return self.Dummy
        else:
            return self.node_template.Dummy

    @property
    def name(self) -> str:
        return self.node_template.name

    def get_params(self, name: str = None, context: str = None) -> dict:
        """Returns all the parameters"""
        params = {}
        _name = name or self.name
        _context = context or self._flow_ref

        for key in self.node_template.Parameter.keys():
            value = self.get_param(key, _name, _context)
            if value is not None:
                params.update({key: value})

        return params

    def get_param(
        self, key: str, name: str = None, context: str = None, custom_parser: any = None
    ) -> any:
        """
        Returns a specific parameter of the node instance after
        parsing it
        """

        _name = name or self.name
        _parser = custom_parser or self.parser

        # main flow context or own context
        _context = context or self._flow_ref

        # get the template value
        tpl_value = self.node_template.get_params().get(key, None)  # Parameter[key].Value

        # get the instance value
        try:
            inst_value = self.Parameter[key].Value
            if inst_value is None:
                # param is disabled, and we return None
                return None

        except KeyError:
            inst_value = None

        _value = tpl_value if inst_value is None else inst_value

        # parse the parameter
        output = _parser.parse(key, str(_value), _name, self, _context)

        if output is None and tpl_value is not None:
            # this means that the instance does not contain a valid parameter. This can also be the case
            # that the user does not want to redefine the template arg and is only overriding the right
            # params. Parse parameter again using template argument
            _value = tpl_value
            output = _parser.parse(key, str(_value), _name, self, _context)
        # the _launch params will need to be calculated only once
        if isinstance(output, bool) and key == "_launch":
            self.Launch = ("override", output)
        return output
