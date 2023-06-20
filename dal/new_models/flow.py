from typing import Optional, Dict, List, Any, Union
from pydantic import constr, BaseModel, validator, ValidationError, Extra
from .base_model import Arg, MovaiBaseModel
import re
from .configuration import Configuration


ValidName = constr(regex=r"^[a-zA-Z0-9_]+$")


class Layer(BaseModel):
    name: Optional[str] = None
    on: Optional[bool] = None


class CmdLineValue(BaseModel):
    Value: Any


class EnvVarValue(BaseModel):
    Value: Any


class Parameter(BaseModel):
    Child: Optional[str] = None
    Parent: Optional[str] = None


class Portfields(BaseModel):
    Message: Optional[str] = None
    Callback: Optional[str] = None
    Parameter: Optional[Parameter] = None


class X(BaseModel):
    Value: float


class Y(BaseModel):
    Value: float


class Visualization(BaseModel):
    x: X
    y: Y


class Visual(BaseModel):
    # __root__: Union[VisualItem, VisualItem1]
    Visualization: Union[List[float], Visualization]


class ContainerValue(BaseModel):
    ContainerFlow: Optional[str] = None
    ContainerLabel: Optional[str] = None
    # Parameter: Optional[ArgSchema] = None
    Parameter: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), Arg]] = None


LINK_REGEX = r"^~?[a-zA-Z_0-9]+(//?~?[a-zA-Z_0-9]+){0,}$"
class Link(BaseModel):
    From: str
    To: str

    @validator('From', 'To', pre=True, always=True)
    def validate_regex(cls, value, field):
        if not re.match(LINK_REGEX, value):
            raise ValueError(f"Field '{field.alias}' with value '{value}' does not match the required pattern '{LINK_REGEX}'.")
        return value
    
PARAMETER_REGEX = r"^(/?[a-zA-Z0-9_@]+)+$"
class NodeInstValue(BaseModel):
    NodeLabel: Optional[ValidName] = None
    Parameter: Optional[Dict[str, Arg]] = None
    Template: Optional[ValidName] = None
    CmdLine: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), CmdLineValue]] = None
    EnvVar: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), EnvVarValue]] = None
    NodeLayers: Optional[Any] = None
    
    @validator('Parameter', pre=True, always=True)
    def validate_regex(cls, value):
        if isinstance(value, dict):
            for key in value:
                if not re.match(PARAMETER_REGEX, key):
                    raise ValueError(f"Field '{Parameter}' with value '{key}' does not match the required pattern '{PARAMETER_REGEX}'.")
        return value


class Flow(MovaiBaseModel, extra=Extra.allow):
    Parameter: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), Arg]] = None
    Container: Optional[Dict[constr(regex=r"^[a-zA-Z_0-9]+$"), ContainerValue]] = None
    ExposedPorts: Optional[
        Dict[
            constr(regex=r"^(__)?[a-zA-Z0-9_]+$"),
            Dict[
                constr(regex=r"^[a-zA-Z_0-9]+$"),
                List[constr(regex=r"^~?[a-zA-Z_0-9]+(\/~?[a-zA-Z_0-9]+){0,}$")],
            ],
        ]
    ] = None
    Layers: Optional[Dict[constr(regex=r"^[0-9]+$"), Layer]] = None
    Links: Optional[Dict[constr(regex=r"^[0-9a-z-]+$"), Link]] = None
    NodeInst: Optional[Dict[constr(regex=r"^[a-zA-Z_0-9]+$"), NodeInstValue]] = None

    def _original_keys(self) -> List[str]:
        return super()._original_keys() + ["Parameter", "Container", "ExposedPorts", "Layers", "Links", "NodeInst"]

    class Meta:
        model_key_prefix = "Flow"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_calc_remaps = None
        self.cache_dict = None
        self.cache_node_insts = {}
        self.cache_node_template = {}
        self.cache_ports_templates = {}
        self.cache_node_params = {}
        self.cache_container_params = {}
        self.parent_parameters = {}

    def eval_config(self, _config: str, *__) -> any:
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

        output = Configuration(_config_name).get_param(_config_param)

        return output

