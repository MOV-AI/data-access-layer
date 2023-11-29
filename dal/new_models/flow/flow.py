from typing import Optional, Dict, List, Any, ClassVar, Set
from pydantic import StringConstraints, Field, BaseModel, ConfigDict
from ..base_model.common import Arg
from ..base import MovaiBaseModel
from ..configuration import Configuration
from .parsers import ParamParser
from ...helpers.flow import GFlow
from types import SimpleNamespace
from .nodeinst import NodeInst as NodeInstClass
from .container import Container as ContainerClass
from .flowlinks import FlowLink
from ..node import Node
from dal.helpers import flatten
from cachetools import LRUCache
from movai_core_shared.consts import ROS1_NODELETSERVER
from typing_extensions import Annotated
import re
from movai_core_shared.exceptions import DoesNotExist
from movai_core_shared.logger import Log

logger = Log.get_logger(__name__)


class Layer(BaseModel):
    name: Optional[str] = None
    on: Optional[bool] = None


class Flow(MovaiBaseModel):
    Parameter: Optional[Dict[Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+$")], Arg]] = None
    Container: Optional[Dict[Annotated[str, StringConstraints(pattern=r"^[a-zA-Z_0-9]+$")], ContainerClass]] = Field(
        default_factory=dict
    )
    ExposedPorts: Optional[
        Dict[
            Annotated[str, StringConstraints(pattern=r"^(__)?[a-zA-Z0-9_]+$")],
            Dict[
                Annotated[str, StringConstraints(pattern=r"^[a-zA-Z_0-9]+$")],
                List[Annotated[str, StringConstraints(pattern=r"^~?/?[a-zA-Z_0-9]+(\/~?[a-zA-Z_0-9]+){0,}$")]],
            ],
        ]
    ] = None
    Layers: Optional[Dict[Annotated[str, StringConstraints(pattern=r"^[0-9]+$")], Layer]] = None
    Links: Optional[Dict[Annotated[str, StringConstraints(pattern=r"^[0-9a-z-]+$")], FlowLink]] = Field(default_factory=dict)
    NodeInst: Optional[Dict[Annotated[str, StringConstraints(pattern=r"^[a-zA-Z_0-9]+$")], NodeInstClass]] = Field(
        default_factory=dict
    )
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

    # allow extra fields to be added dynamically after creation of object
    model_config = ConfigDict(extra="allow")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs and self.scope in kwargs:
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

    def get_dict(self, data: dict = None, prefix: str = None, prev_flows: list = None) -> dict:
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
            raise RecursionError("Flow already in use, this will lead to infinite recursion")

        # start creating the dict
        output = data or self._with_prefix("", self.NodeInst.items(), self.Links.items())

        for _, container in self.Container.items():
            # container.ContainerFlow is expected to have the full path of the doc
            subflow = Flow(container.ContainerFlow)

            # update prefix
            _prefix = f"{prefix}__" if prefix else ""
            label = f"{_prefix}{container.ContainerLabel}"

            # extract subflow data
            wprefix = subflow._with_prefix(label, subflow.NodeInst.items(), subflow.Links.items())

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
            raise KeyError(f"Node instance '{name}' does not exist in '{self.pk}'") from e

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
            if Flow.__START__ == port_from.str.upper() or Flow.__END__ == port_to.str.upper():
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
        dependencies = self.get_node_dependencies(node_name=node_inst, first_level_only=True)

        for dependency in dependencies:
            # get the node instance
            node_inst_dep = self.get_node_inst(dependency)

            # check if it is a plugin
            if node_inst_dep.is_plugin:
                output.add(dependency)

        return output

    @staticmethod
    def exposed_ports_diff(previous_ports: dict, current_ports: dict) -> list:
        """
        Returns deleted exposed ports by subtracting ports
        in current_ports from the previous_ports

        Parameters:
            previous_ports (dict): dictionary with previous ports
            current_ports (dict): dictionary with current ports

        Returns:
            (list): list of dictionaries with the ports to delete

        previous_ports and current_ports format:
            {
                <node_template_or_flow_name>:
                    {
                        <node_instance_name>: [<port_name1>, ..., <port_nameN>]
                    }
            }
        """

        # character used in the construction of the path
        # usign comma because it cannot be used in the name of the nodes and ports
        path_char = ","

        # flatten the previous ports
        res1 = flatten(previous_ports, [], "", path_char)

        # flatten the current ports
        res2 = flatten(current_ports, [], "", path_char)

        # removing current_ports from the previous_ports will return ports to delete
        diff = set(res1) - set(res2)

        to_delete = {}

        # convert diff back to initial format
        for port_to_delete in diff:

            template, node_instance, port = port_to_delete.split(path_char)

            to_delete.setdefault(template, {}).setdefault(node_instance, []).append(
                port
            )

        return [{key: value} for key, value in to_delete.items()]

    @staticmethod
    def on_flow_delete(flow_id: str):
        """
        Actions to do when a flow is deleted
        - Delete all nodes of type Container with ContainerFlow = flow_id
        """

        for flow in Flow.find():
            flow: Flow = flow
            for c_name, c_value in flow.Container.items():
                if c_value.ContainerFlow == flow_id:
                    flow.delete_part("Container", c_name)

    def __getTemplate(self, key: str, name: str) -> str:
        """returns the template name (NodeInst) or flow name (Container)
        Args:
            key: NodeInst or Container
            name: instance name

        Return:
            template name or None
        """
        template_keys = {"NodeInst": "Template", "Container": "ContainerFlow"}

        # get all NodeInst(s) or Container(s)
        _instances = getattr(self, key)

        # get the specific NodeInst or Container
        _inst = _instances.get(name)

        # get the template based on the type
        _template = getattr(_inst, template_keys[key], None)

        # add prefix based on the type
        # Containers should add __ to the template name
        prefix = "__" if key == "Container" else ""

        # build the template name
        if _template:
            return f"{prefix}{_template}"

    def delete_part(self, key: str, name: str):
        """Delete object dependencies"""

        template = self.__getTemplate(key, name)
        self.Container.get(name)

        try:
            # delete NodeInst or Container Links
            if key in ["NodeInst", "Container"]:

                # string to check will be nodeInst1/nodeInst2
                # name can be nodeInst or nodeInst__otherName
                pattern = re.compile(f"^{name}/.+|^{name}__.*/|/{name}$|/{name}__.*$")

                for link, value in self.Links.items():
                    values = [
                        prop.node_inst for prop in [value.From, value.To]
                    ]

                    # join the values into one string
                    # if pattern found delete link
                    if pattern.findall("/".join(values)):
                        del self.Links[link]

                exposed_ports_dict = self.ExposedPorts.get(template, None)

                # delete node exposed ports
                if self.delete_exposed_port(template, "*", name):
                    # we want to delete links only if there was exposed ports.
                    if exposed_ports_dict:
                        for port in exposed_ports_dict.get(name, []):
                            self.delete_exposed_port_links(name, port)

        except Exception as error:
            logger.error(str(error))
            return False

        return True

    def delete_exposed_port(
        self, node_id: str, port_name: str = "*", node_inst_id: str = None
    ) -> bool:
        """Delete exposed port
        Args:
            node_id: Node template name
            port_name: port name to delete or * to delete all
            node_inst_id: delete only ports related w/ specific node instance

        Info:
            ExposedPorts is of type hash
                - key (str) is the name of the Node (Template)
                - value (dict) format is {"<NodeInst>": ["Ports"]}

        Returns:
            True for success, False otherwise.
        """
        try:
            exposed_ports = {**self.ExposedPorts}
            ports_deleted = {}

            if not exposed_ports or node_id not in exposed_ports:
                raise DoesNotExist

            for node_inst, ports in self.ExposedPorts.get(node_id, {}).items():
                # delete only node_inst_id ports
                if node_inst_id is not None and node_inst != node_inst_id:
                    continue

                for port in ports:
                    re_port = re.search(r"^.+/", port)[0][:-1]

                    # delete specific port or all (*)
                    if port_name in (re_port, "*"):
                        exposed_ports[node_id][node_inst].remove(port)

                        # add deleted port to list
                        ports_deleted.setdefault(node_inst, [])
                        ports_deleted[node_inst].append(port)

                        if not exposed_ports[node_id][node_inst]:
                            # remove NodeInst if list of ports is empty
                            del exposed_ports[node_id][node_inst]

            if exposed_ports[node_id].keys():
                # update dictionary value
                self.ExposedPorts.update(exposed_ports)
            else:
                # key (Node) value is empty
                del self.ExposedPorts[node_id]

            self.save()

            return True

        except DoesNotExist:
            # No exposed ports...
            pass

        except Exception as e:
            logger.error(str(e))

        return False

    #  NOT PORTED ->  move it to class Link
    def delete_exposed_port_links(
        self,
        node_inst_name: str,
        port_name: str,
        join_char: str = None,
        prefix: str = None,
        flows: dict = None,
    ) -> bool:
        """
        Find all links in all Flows with containers and delete links to the exposed port
        Also deletes exposed ports

        Args:
            node_inst_name (str): The name of the node instance.
            port_name (str): The unexposed port name.
            join_char (str): '/' when starting from a node instance or '__' when starting from a subflow
            prefix (str): Node instance name when going to upper flows.
            flows (dict): List of flows with subflows.

        Returns:
            bool: True for success, False otherwise.

        """

        # get info about flows with containers
        flows_with_containers: List[Flow] = []
        for flow in Flow.find():
            flow: Flow = flow
            if flow.Container:
                flows_with_containers.append(flow)

        # Loop flows that have subflows
        for flow in flows_with_containers:
            # Loop throught subflows
            for flow_container in next(iter(flow.Container.values())):
                flow_container: ContainerClass = flow_container

                # check if the subflow is referencing me
                if flow_container.ContainerFlow == self.name:
                    try:

                        container_label = flow_container.ContainerLabel
                        _port_prefix = (
                            f"{container_label}__{prefix}"
                            if prefix
                            else container_label
                        )

                        _join_char = join_char or (
                            "__"
                            if (self.Container.get(node_inst_name, None) or prefix)
                            else "/"
                        )

                        # we do not care about the in/out of the port bc port names are unique in the Node
                        regex = re.compile(rf"{_port_prefix}__{node_inst_name}{_join_char}{port_name}/.+")

                        # delete the link associated with the port
                        for link_id, link in flow.Links.items():
                            _to = link.To
                            _from = link.From
                            if regex.match(_to) or regex.match(_from):
                                del flow.Links[link_id]

                        # delete the exposed port
                        # __<Flow name> is how we identify flows in the exposed ports
                        if f"__{self.name}" in flow.ExposedPorts.keys():

                            def format_port(pfx, nnm, pnm):
                                return f"{pfx}__{nnm}/{pnm}" if pfx else f"{nnm}/{pnm}"

                            # _port_name = port_name
                            # if _port_name is not "*":
                            #     _port_name = f"{prefix}__{node_inst_name}/{port_name}" if prefix else f'{node_inst_name}/{port_name}'
                            _port_name = (
                                format_port(prefix, node_inst_name, port_name)
                                if port_name != "*"
                                else port_name
                            )

                            flow.delete_exposed_port(
                                f"__{self.name}", _port_name, container_label
                            )

                        # check Flows using 'flow' as a subflow
                        flow.delete_exposed_port_links(
                            node_inst_name,
                            port_name,
                            _join_char,
                            _port_prefix,
                            flows_with_containers,
                        )

                    except Exception as e:
                        logger.error(str(e))

            flow.save()

        return True
