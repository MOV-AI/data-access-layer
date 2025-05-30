"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva  (manuel.silva@mov.ai) - 2020
"""
from typing import TYPE_CHECKING, Any, Optional

from .scopestree import ScopeObjectNode, ScopeNode, scopes

if TYPE_CHECKING:
    from dal.models.flow import Flow


class Container(ScopeObjectNode):
    """
    A container represents a flow in another flow (aka subflow)
    """

    ContainerLabel: str
    ContainerFlow: str

    @property
    def flow(self) -> "Flow":
        """Returns the parent flow instance (Flow)"""
        return self.parent.parent

    @property
    def subflow(self) -> "Flow":
        """Returns the flow instance (Flow) represented by the container"""
        return scopes.from_path(self.ContainerFlow, scope="Flow")

    @property
    def parser(self):
        """Get the parser (GParser) from the parent"""
        return self.parent.parent.parser

    def get_node_inst(self, key: str):
        """
        Returns a node instance (NodeInst) inside the flow represented by the container
        """
        return self.flow.NodeInst[key]

    def get_params(self, name: str = None) -> dict:
        """Returns all the parameters"""
        params = {}
        _name = name or self.name

        for key in self.Parameter.keys():
            params.update({key: self.get_param(key, _name)})

        return params

    def get_param(
        self,
        key: str,
        name: Optional[str] = None,
        context: Optional[str] = None,
        custom_parser: Optional[Any] = None,
        default_value: Optional[Any] = None,
    ) -> Any:
        """
        Returns a specific parameter of the container after
        parsing it
        """

        _name = name or self.name

        # get the parser instance
        _parser = custom_parser or self.parser

        # main flow context or own context
        _context = context or self.flow.ref

        try:
            _value = self.Parameter[key].Value
        except KeyError:
            _value = default_value

        # parse the parameter
        output = _parser.parse(key, str(_value), _name, self, _context)

        return output


ScopeNode.register_scope_object("schemas/1.0/Flow/Container", Container)
