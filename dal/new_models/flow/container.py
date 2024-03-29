"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2023
"""
from typing import Optional, Dict, Union, List
from typing_extensions import Annotated

from pydantic import StringConstraints, ConfigDict, Field, BaseModel

from dal.new_models.base_model.common import Arg


class X(BaseModel):
    Value: float


class Y(BaseModel):
    Value: float


class Visualization(BaseModel):
    """A class that implements the Visualization field"""

    x: X
    y: Y


class Container(BaseModel):
    """A class that implements the Container field"""

    ContainerFlow: str = ""
    ContainerLabel: str = ""
    Parameter: Optional[
        Dict[Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+$")], Arg]
    ] = Field(default_factory=dict)
    Visualization: Union[List[float], Visualization]
    model_config = ConfigDict(extra="allow")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parser = None
        self._flow_class = None

    def model_dump(
        self,
        *,
        include=None,
        exclude=None,
        by_alias: bool = False,
        skip_defaults: Optional[bool] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,
    ):
        dic = super().model_dump(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        dic.pop("_parser")
        dic.pop("_flow_class")
        return dic

    @property
    def flow(self):
        """Returns the parent flow instance (Flow)"""
        return self._parser.flow

    @property
    def subflow(self):
        """Returns the flow instance (Flow) represented by the container"""
        if self.ContainerFlow and self._flow_class:
            try:
                obj = self._flow_class(self.ContainerFlow)
                return obj
            except Exception as exc:
                self._logger(
                    f"Got exception of type: {exc} while trying to load the object: {self.ContainerFlow}"
                )
                return None

    @property
    def parser(self):
        """Get the parser (GParser) from the parent"""
        return self._parser

    def get_node_inst(self, key: str):
        """
        Returns a node instance (NodeInst) inside the flow represented by the container
        """
        return self.flow.NodeInst[key]

    def get_params(self, name: str = None) -> dict:
        """Returns all the parameters"""
        params = {}
        _name = name or self.subflow.name

        for key in self.Parameter.keys():
            params.update({key: self.get_param(key, _name)})

        return params

    def get_param(self, key: str, name: str = None, context=None, custom_parser: any = None) -> any:
        """
        Returns a specific parameter of the container after
        parsing it
        """

        _name = name or self.subflow.name

        # get the parser instance
        _parser = custom_parser or self.parser

        # main flow context or own context
        _context = context or self.flow.name

        try:
            _value = self.Parameter[key].Value
        except KeyError:
            _value = None

        # parse the parameter
        output = _parser.parse(key, str(_value), _name, self, _context)

        return output
