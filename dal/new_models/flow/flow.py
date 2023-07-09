from typing import Optional, Dict, List, Any, Union, ClassVar, Set
from pydantic import Field, constr, BaseModel, Extra
from ..base_model import Arg, MovaiBaseModel
from ..configuration import Configuration
from .parsers import ParamParser
from ...helpers.flow import GFlow
from types import SimpleNamespace
from .nodeinst import NodeInst as NodeInstClass
from .container import Container as ContainerClas
from .flowlinks import FlowLink
from ..node import Node
from cachetools import LRUCache
from movai_core_shared.consts import ROS1_NODELETSERVER


class Layer(BaseModel):
    name: Optional[str] = None
    on: Optional[bool] = None


class Flow(MovaiBaseModel, extra=Extra.allow):
    Parameter: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), Arg]] = None
    Container: Optional[Dict[constr(regex=r"^[a-zA-Z_0-9]+$"), ContainerClas]] = Field(default_factory=dict)
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
    Links: Optional[Dict[constr(regex=r"^[0-9a-z-]+$"), FlowLink]] = Field(default_factory=dict)
    NodeInst: Optional[Dict[constr(regex=r"^[a-zA-Z_0-9]+$"), NodeInstClass]] = Field(default_factory=dict)
    __START__: ClassVar[str] = "START/START/START"
    __END__: ClassVar[str] = "END/END/END"

    def _original_keys(self) -> List[str]:
        return super()._original_keys() + [
            "Parameter",
            "Container",
            "ExposedPorts",
            "Layers",
            "Links",
            "NodeInst",
        ]

    class Meta:
        model_key_prefix = "Flow"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs:
            self._parser = ParamParser(self)
            self._graph = GFlow(self)
            self._full = None
            self._links_cache = LRUCache(maxsize=100)
            if self.NodeInst:
                for _, node_inst in self.NodeInst.items():
                    node_inst._parser = self._parser
                    node_inst._flow_ref = self.name
            if self.Links:
                for _, link in self.Links.items():
                    link._parser = self._parser
            if self.Container:
                for _, container in self.Container.items():
                    container._parser = self._parser
                    container._flow_class = Flow

    @property
    def full(self) -> dict:
        """Returns the data from the main flow and all subflows"""
        self._full = self._full or self.get_dict()
        return self._full

    @property
    def parser(self) -> ParamParser:
        """Get or create and instance of the parser"""
        return self._parser

    @property
    def graph(self) -> GFlow:
        """Get or create an instance of the graph generator"""
        return self._graph

    @property
    def remaps(self) -> dict:
        """Get remaps from the graph instance"""
        return self._graph.get_remaps()

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

    @property
    def parser(self) -> ParamParser:
        """Get or create and instance of the parser"""

        self._parser = self._parser or ParamParser(self)
        return self._parser

    @classmethod
    def _with_prefix(cls, prefix: str, nodes: dict, links: dict) -> SimpleNamespace:
        """ "
        Add a prefix to the node instances and also to the links
        """
        output = SimpleNamespace(NodeInst={}, Links={})

        prefix = f"{prefix}__" if prefix else ""

        for _id, node_inst in nodes:
            pref_id = f"{prefix}{_id}"

            output.NodeInst.update({pref_id: node_inst})

        for _id, value in links:
            _value = {}
            pref_id = f"{prefix}{_id}"

            _value["From"] = (
                f"{prefix}{value.From.str}"
                if value.From.str.upper() != Flow.__START__
                else value.From.str
            )
            _value["To"] = f"{prefix}{value.To.str}"
            _value["Dependency"] = value.Dependency

            # required for legacy compatibility
            output.Links.update({pref_id: FlowLink(**_value)})

        return output

    def get_dict(
        self, data: dict = None, prefix: str = None, prev_flows: list = None
    ) -> dict:
        """
        Aggregate data from the main flow and subflows
        Returns a dictionary with the following format
        {
            "NodeInst": {
                { <node instance name with parents prefix>: {"ref": <ref to node_inst instance>}
            }
            "Links": {
                {<link id w/ parents prefix>: {"From": <link w/ prefix>, "To": <link w/ prefix>}}
            }
        }

        """
        prev_flows = prev_flows or []

        if self.pk in prev_flows:
            raise RecursionError(
                "Flow already in use, this will lead to infinite recursion"
            )

        # start creating the dict
        output = data or self._with_prefix(
            "", self.NodeInst.items(), self.Links.items()
        )

        for _, container in self.Container.items():
            # container.ContainerFlow is expected to have the full path of the doc
            subflow = Flow(container.ContainerFlow)

            # update prefix
            _prefix = f"{prefix}__" if prefix else ""
            label = f"{_prefix}{container.ContainerLabel}"

            # extract subflow data
            wprefix = subflow._with_prefix(
                label, subflow.NodeInst.items(), subflow.Links.items()
            )

            # update main dict
            output.NodeInst.update(wprefix.NodeInst)
            output.Links.update(wprefix.Links)

            # append current flow to the list of flows already in use
            prev_flows.append(self.pk)

            subflow.get_dict(output, label, prev_flows.copy())

        return output

    def get_node_params(self, node_name: str, context: str = None) -> dict:
        """Returns the parameters of the node instance"""

        # TODO rename to get_node_inst_params ?

        # in the context of a another flow or own context
        _context = context or self.name
        node_inst = self.get_node_inst(node_name)
        return node_inst.get_params(node_name, _context)

    def get_node_inst(self, name: str) -> NodeInstClass:
        """
        Returns a node instance from full flow (subflows included)
        """
        # format:
        # {"NodeLabel" <>, ref": <NodeInst object>}

        try:
            return self.full.NodeInst[name]

        except KeyError as e:
            raise KeyError(
                f"Node instance '{name}' does not exist in '{self.pk}'"
            ) from e

    def get_container(self, name: str, context: str = None):
        """Returns an instance of Container"""

        # each element represents a container, aka subflow
        node_name_arr = name.split("__")

        _container = None
        _flow = self

        # the context is used to get back to the main flow while
        # checking the parameters of a node instance in a subflow
        if context:
            _flow = Flow(context)

        # going up to the main flow using the context allows
        # to get the container down in a subflow
        for ctr in node_name_arr:
            _container = _flow.Container[ctr]

            _flow = _container.subflow

        return _container

    def get_node(self, node_inst_name: str) -> Node:
        """
        Returns an instance of Node (template)
        """
        # TODO check if method is still in use

        return self.NodeInst[node_inst_name].node_template

    def get_start_nodes(self) -> list:
        """
        Returns all node instances with a link to the START node
        """

        output = []

        for link_id in self.full.Links.keys():
            link = self.full.Links[link_id]

            # node is connected to the start block
            if link.From.str.upper() == Flow.__START__:
                output.append(link.To.node_inst)

        return output

    def get_param(self, key: str, context: str = None) -> any:
        """
        Returns a parameter of the flow after parsing it
        """

        # get the flow parameter
        try:
            param = self.Parameter[key].Value
        except KeyError:
            return None

        # main flow context or own context
        _context = context or self.name

        # parse the parameter in the context of "_context"
        output = self.parser.parse(key, param, context=_context)

        return output

    def get_node_inst_param(self, name: str, key: str, context: str = None) -> Any:
        """Returns the node instance parameter"""
        _context = context or self.name

        return self.get_node_inst(name).get_param(key, name, _context)

    def get_lifecycle_nodes(self) -> list:
        """List of Ros2 Lifecycle Nodes"""
        output = []

        for _, node_inst in self.full.NodeInst.items():
            # if node_inst.Type == ROS2_LIFECYCLENODE:
            #    output.append(node_inst.ref)
            # FIXME not being used and causing bugs
            pass

        return output

    def get_node_links(self, node_name: str) -> list:
        """Returns the node instance links in the flow and subflows"""
        links_key = f"{self.path}::links::{node_name}"
        if links_key in self._links_cache:
            return self._links_cache[links_key]
        links = []

        """
        {<link id w/ parents prefix>: {"From": <link w/ prefix>, "To": <link w/ prefix>}} 
        """
        for key in self.full.Links:
            link = self.full.Links[key]

            if node_name in [link.From.node_inst, link.To.node_inst]:
                _type = "From" if node_name == link.From.node_inst else "To"
                _link = {"Type": _type, "ref": link, "id": key}

                links.append(_link)
        self._links_cache[links_key] = links
        return links

    def get_node_transitions(self, node_name: str, port_name: str = None) -> Set[str]:
        """Returns a list of nodes to transit to"""

        transition_nodes = set()

        # get the node_inst node template
        node_tpl = self.get_node_inst(node_name).node_template

        # get all the links of the node_inst
        links = self.get_node_links(node_name)

        for link in links:
            _type = link["Type"]  # From or To
            # TODO confirm this fix
            if _type == "To":
                continue
            flow_link: FlowLink = link["ref"]
            _plink = getattr(flow_link, _type)  # Get partial link from ref
            _port_type = "In" if _type == "To" else "Out"

            # get the Ports instance from the Node template
            port_tpl = node_tpl.get_port(_plink.port_name)

            def filter_by_port(fnport, lnport):
                return True if fnport is None else fnport == lnport

            if port_tpl.is_transition(_port_type, _plink.port_type) and filter_by_port(
                port_name, _plink.port_name
            ):
                # get the node_inst to transit to
                to_transit = flow_link.From if _type == "To" else flow_link.To

                # FIXME give as models.NodeInst object
                transition_nodes.add(to_transit.node_inst)

        # TODO output is including every node instance even with no transition possible (iport).
        return transition_nodes

    def get_nodelet_manager(self, node_inst: str) -> str:
        """Returns nodelet manager name"""
        output = None

        # get the node_inst instance ref
        node_inst_ref = self.get_node_inst(node_inst)

        # node instance is not of type nodelet
        if not node_inst_ref.is_nodelet:
            return output

        # get all the links of the node_inst
        links = self.get_node_links(node_inst)

        for link in links:
            if link["ref"].From.node_inst != node_inst:
                continue

            # Get the manager part (To)
            _plink = link["ref"].To

            # get the node inst manager
            node_inst_mng = self.get_node_inst(_plink.node_inst)

            # get the node inst template
            node_tpl_mng = node_inst_mng.node_template

            # check the Ports instance from the Node template
            if node_tpl_mng.PortsInst[_plink.port_name].Template == ROS1_NODELETSERVER:
                return _plink.node_inst

        return output

    def get_node_dependencies(
        self,
        node_name: str,
        dependencies_collected: list = None,
        links_to_skip: list = None,
        skip_parent_node: set = None,
        first_level_only: bool = False,
    ) -> list:
        """Get node dependencies recursively"""

        # TODO review and refactor

        dependencies = dependencies_collected or []

        links_to_skip = links_to_skip or []

        # do not include node_name as a dependency
        skip_parent_node = skip_parent_node or set()
        skip_parent_node.add(node_name)

        node_transitions = self.get_node_transitions(node_name)

        links = self.get_node_links(node_name)

        for link in links:
            if link["id"] in links_to_skip:
                continue

            # link dependencies level
            # 0: check dependencies in both directions (From and To)
            # 1: check dependencies only From -> To
            # 2: check dependencies only To -> From
            # 3: do not check dependencies
            dependencies_level = link["ref"].Dependency

            # do not check link dependencies
            if dependencies_level == 3:
                continue

            port_from = link["ref"].From
            port_to = link["ref"].To

            dependencies_from_to = dependencies_level in (0, 1)
            dependencies_to_from = dependencies_level in (0, 2)

            dependency_name = None

            # start is not a dependency
            if (
                Flow.__START__ == port_from.str.upper()
                or Flow.__END__ == port_to.str.upper()
            ):
                links_to_skip.append(link["id"])
                continue

            if node_name == port_from.node_inst and dependencies_from_to:
                dependency_name = port_to.node_inst
            if node_name == port_to.node_inst and dependencies_to_from:
                dependency_name = port_from.node_inst

            if dependency_name is not None and dependency_name not in skip_parent_node:
                # transition nodes are not considered as dependencies
                if dependency_name in node_transitions:
                    continue
                if self.get_node_inst(dependency_name).is_state:
                    continue
                if dependency_name not in dependencies:
                    # skip link prevents never ending recursion
                    links_to_skip.append(link["id"])
                    dependencies.append(dependency_name)
                    if not first_level_only:
                        dependencies = self.get_node_dependencies(
                            dependency_name,
                            dependencies,
                            links_to_skip,
                            skip_parent_node,
                        )

        return list(set(dependencies))

    def get_node_plugins(self, node_inst: str) -> set:
        """Return NodeInst(s) plugins linked to node_inst"""

        output = set()

        # get first level node dependencies
        dependencies = self.get_node_dependencies(
            node_name=node_inst, first_level_only=True
        )

        for dependency in dependencies:
            # get the node instance
            node_inst_dep = self.get_node_inst(dependency)

            # check if it is a plugin
            if node_inst_dep.is_plugin:
                output.add(dependency)

        return output
