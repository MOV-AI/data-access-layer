"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020

    Module that implements a Node scope class
"""

import re
from movai_core_shared.consts import (
    MOVAI_NODE,
    MOVAI_SERVER,
    MOVAI_STATE,
    MOVAI_TRANSITIONFOR,
    MOVAI_TRANSITIONTO,
    ROS1_NODE,
    ROS1_NODELET,
    ROS1_PLUGIN,
)
from dal.movaidb import MovaiDB
from dal.scopes.scope import Scope
from dal.helpers import Helpers
from movai_core_shared.logger import Log

LOGGER = Log.get_logger(__name__)


class Node(Scope):
    """Node class"""

    scope = "Node"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Node", name=name, version=version, new=new, db=db)

    def is_valid(self):
        # what is in db is valid to run
        # need to have: Info, Version, Type, 1+ PortsInst, Path if Type==ROS1
        return True

    def set_type(self):
        ports = MovaiDB().get(
            {"Node": {self.name: {"PortsInst": {"*": {"Template": "*"}}}}}
        )
        path = MovaiDB().get_value({"Node": {self.name: {"Path": ""}}})
        type_to_set = MOVAI_NODE
        templs = []
        if ports:
            for _, temp in ports["Node"][self.name]["PortsInst"].items():
                templs.append(temp["Template"])
        if path:
            if any("ROS1/PluginClient" in templ for templ in templs):
                type_to_set = ROS1_PLUGIN
            else:
                type_to_set = ROS1_NODE

        if any("ROS1/Nodelet" in templ for templ in templs):
            type_to_set = ROS1_NODELET

        if any("Http" in templ for templ in templs):
            type_to_set = MOVAI_SERVER

        if any(templ in (MOVAI_TRANSITIONFOR, MOVAI_TRANSITIONTO) for templ in templs):
            type_to_set = MOVAI_STATE

        MovaiDB().set({"Node": {self.name: {"Type": type_to_set}}})

    def get_params(self, attribute="Parameter"):
        final_params = {}
        node_name = self.name
        params = MovaiDB().get({"Node": {node_name: {attribute: {"*": {"Value": ""}}}}})

        if params:
            for param, _value in params["Node"][node_name][attribute].items():
                value = _value["Value"]
                value = self.get_ref(value)
                final_params[param] = value
        return final_params

    def is_state(self):
        if self.Type == MOVAI_STATE:
            return True
        return False

    def is_persistent(self):
        if not self.Persistent:
            return False
        return True

    def is_port_remappable(self, portinst):

        remappable = self.PortsInst[portinst].Remappable
        if remappable is None:
            return True
        return remappable

    def delete(self, key, name, force=False):

        if key in ["PortsInst", "PortInst"]:
            # If PortsInst then search for Flow links where the port exists and delete those entries
            from dal.scopes.flow import Flow

            dependencies = self.port_inst_depends(name)
            for dependence in dependencies:
                try:
                    flow_name = next(iter(dependence.get("Flow").keys()))

                    dep_keys = dependence.get("Flow").get(flow_name).keys()
                    try:
                        if "Links" in dep_keys:
                            links_dict = (
                                dependence.get("Flow").get(flow_name).get("Links")
                            )
                            link_id = next(iter(links_dict.keys()))
                            Flow(flow_name).delete_link(link_id)
                        elif "ExposedPorts" in dep_keys:
                            Flow(flow_name).delete_exposed_port(self.name, name)
                    except Exception:
                        # flow does not exist; probably a reference to a flow in the archive
                        pass

                except Exception as e:
                    LOGGER.error(str(e))

        super().delete(key, name)

    def remove(self, force=False) -> bool:

        # Check if Node has instances on existing Flows
        node_inst_ref_keys = self.node_inst_depends()

        # Check if Node Ports has instances on existing Flows
        ports_inst = {}
        has_port_inst_dependencies = False
        for port_inst_name in self.PortsInst.keys():
            port_node_instance_links = self.get_port_node_instance_links(
                port_name=port_inst_name
            )
            ports_inst[port_inst_name] = port_node_instance_links
            has_port_inst_dependencies = (
                True
                if not has_port_inst_dependencies and port_node_instance_links
                else False
            )

        if not force and (node_inst_ref_keys or has_port_inst_dependencies):
            raise ValueError(
                "The Node has dependencies, use force=True to force deletion of Node and all its dependencies."
            )

        try:
            # If force=True remove Node, all Node instances on Flows and Node Ports and Links
            result = False
            if force:
                for port_inst in ports_inst:
                    self.delete(key="PortsInst", name=port_inst)

                from dal.scopes.flow import Flow

                for node_inst_ref_key in node_inst_ref_keys:
                    flow_name = next(iter(node_inst_ref_key.get("Flow")))
                    node_inst_name = next(
                        iter(
                            node_inst_ref_key.get("Flow").get(flow_name).get("NodeInst")
                        )
                    )

                    try:
                        flow_obj = Flow(name=flow_name)
                        flow_obj.delete(key="NodeInst", name=node_inst_name)
                    except Exception:
                        # flow does not exist; probably a reference to a flow in the archive
                        pass

            super().remove()
            result = True
        except Exception as e:
            LOGGER.error(str(e))

        return result

    def rename(self, key, old_name, new_name):

        if key == "PortsInst":
            old_depends, _ = self.port_inst_depends(old_name)

            new_depends = eval(
                str(old_depends).replace("/" + old_name + "/", "/" + new_name + "/")
            )

            super().rename(key, old_name, new_name)

            MovaiDB().rename(old_depends, new_depends)

            return True

        super().rename(key, old_name, new_name)

    def template_depends(self, force=False):  # TODO use Links hash

        # this will give a list of tuples (flow_name, node_inst_name)
        deleted_nodes = []
        # this will give a list of tuples (flow_name, link_id?)
        deleted_links = []

        full_dict_to_delete = {"Flow": {}}

        full_node_list = MovaiDB().search(
            {"Flow": {"*": {"NodeInst": {"*": {"Template": self.name}}}}}
        )

        for node_key in full_node_list:
            node = MovaiDB().keys_to_dict([(node_key, "")])
            for flow in node["Flow"]:
                flow_name = flow
            for name in node["Flow"][flow_name]["NodeInst"]:
                node_inst_name = name

            deleted_nodes.append((flow_name, node_inst_name))

            node_dict = MovaiDB().search_by_args(
                "Flow", Name=flow_name, NodeInst=node_inst_name
            )

            try:
                full_dict_to_delete["Flow"][flow_name]["NodeInst"].update(
                    node_dict[0]["Flow"][flow_name]["NodeInst"]
                )
            except:  # First Node Inst for this flow
                full_dict_to_delete["Flow"].update(node_dict[0]["Flow"])

            links_from = MovaiDB().search(
                {
                    "Flow": {
                        flow_name: {"Link": {"*": {"From": "*" + node_inst_name + "*"}}}
                    }
                }
            )
            links_to = MovaiDB().search(
                {
                    "Flow": {
                        flow_name: {"Link": {"*": {"To": "*" + node_inst_name + "*"}}}
                    }
                }
            )

            for link in links_from + links_to:
                for link_id in MovaiDB().keys_to_dict([(link, "")])["Flow"][flow_name][
                    "Link"
                ]:
                    deleted_links.append((flow_name, link_id))

                    links_dict = MovaiDB().search_by_args(
                        "Flow", Name=flow_name, Link=link_id
                    )
                    try:
                        full_dict_to_delete["Flow"][flow_name]["Link"].update(
                            links_dict[0]["Flow"][flow_name]["Link"]
                        )
                    except:  # First Link for this flow
                        full_dict_to_delete["Flow"][flow_name].update(
                            links_dict[0]["Flow"][flow_name]
                        )

        if force:
            MovaiDB().delete(full_dict_to_delete)
            return "True"

        if not deleted_nodes and not deleted_links:
            super().remove()
            return {
                "event": "delete",
                "data": {"numberDependencies": 0, "dependencies": {}},
            }

        dependencies = {}

        for elem in deleted_nodes:
            try:
                dependencies[elem[0]].append({"NodeInst": elem[1]})
            except:
                dependencies.update({elem[0]: []})
                dependencies[elem[0]].append({"NodeInst": elem[1]})

        for elem in list(set(deleted_links)):
            from_ = (
                MovaiDB()
                .search({"Flow": {elem[0]: {"Link": {elem[1]: {"From": "*"}}}}})[0]
                .rsplit(":", 1)[1]
            )
            to_ = (
                MovaiDB()
                .search({"Flow": {elem[0]: {"Link": {elem[1]: {"To": "*"}}}}})[0]
                .rsplit(":", 1)[1]
            )
            try:
                dependencies[elem[0]].append({"from": from_, "to": to_})
            except:
                dependencies.update({elem[0]: []})
                dependencies[elem[0]].append({"from": from_, "to": to_})

        to_return = {
            "event": "warning",
            "data": {
                "numberDependencies": len(set(deleted_links)),
                "dependencies": dependencies,
            },
        }

        return to_return

    def get_port_node_instance_links(self, port_name: str) -> list:

        full_node_list = MovaiDB().search(
            {"Flow": {"*": {"NodeInst": {"*": {"Template": self.name}}}}}
        )

        node_ref_keys = []
        for node_key in full_node_list:
            try:
                # Get flow_name and node_inst_name
                node = MovaiDB().keys_to_dict([(node_key, "")])
                flow_name = next(iter(node.get("Flow").keys()))

                # get Links from Flow(flow_name)
                flow_links = MovaiDB().get({"Flow": {flow_name: {"Links": "*"}}})
                node_inst_name = next(
                    iter(node.get("Flow").get(flow_name).get("NodeInst"))
                )

                for key, value in (
                    flow_links.get("Flow", {})
                    .get(flow_name, {})
                    .get("Links", {})
                    .items()
                ):

                    if re.search(
                        r"^{0}/{1}/.+$".format(node_inst_name, port_name),
                        value.get("From"),
                    ):
                        dict_key = {"Flow": {flow_name: {"Links": {key: value}}}}
                        node_ref_keys.append(dict_key)

                    if re.search(
                        r"^{0}/{1}/.+$".format(node_inst_name, port_name),
                        value.get("To"),
                    ):
                        dict_key = {"Flow": {flow_name: {"Links": {key: value}}}}
                        node_ref_keys.append(dict_key)

            except AttributeError as e:
                LOGGER.error(str(e))

        return node_ref_keys

    def node_inst_depends(self) -> list:
        """Search Flows for NodeInstances"""

        # Check if Node has instances on existing Flows
        flows = MovaiDB().get({"Flow": {"*": {"NodeInst": "*"}}})
        node_inst_ref_keys = []
        if not flows or flows.get("Flow") is None or len(flows.get("Flow")) == 0:
            return node_inst_ref_keys

        for flow_name, node_insts in flows.get("Flow").items():
            for node_inst_name, params in node_insts.get("NodeInst").items():
                if params.get("Template") == self.name:
                    dict_key = {
                        "Flow": {flow_name: {"NodeInst": {node_inst_name: "*"}}}
                    }
                    node_inst_ref_keys.append(dict_key)

        return node_inst_ref_keys

    def port_inst_depends(self, port_name: str) -> list:
        """Loop through NodeInst's Links and return list with matching links dict_keys"""

        # Loop through Flows with ExposedPorts to check if the port is exposed
        flow_exposed_ports = MovaiDB().get({"Flow": {"*": {"ExposedPorts": "*"}}})
        exposed_ports_ref_keys = []
        if (
            not flow_exposed_ports
            or flow_exposed_ports.get("Flow") is None
            or len(flow_exposed_ports.get("Flow")) == 0
        ):
            return exposed_ports_ref_keys
        for key, value in flow_exposed_ports.get("Flow").items():
            exposed_ports = value.get("ExposedPorts").get(self.name, [])
            if not exposed_ports:
                continue

            ports = next(iter(exposed_ports.values()))

            for port in ports:
                re_port = re.search(r"^.+/", port)[0][:-1]
                if re_port == port_name:
                    node_inst_name = next(iter(exposed_ports))
                    dict_key = {
                        "Flow": {key: {"ExposedPorts": {node_inst_name: [port]}}}
                    }
                    exposed_ports_ref_keys.append(dict_key)
                    break

        # Loop through Flows with Containers instances and get Links to the port that is exposed
        flow_container_link_keys = []
        for exposed_port in exposed_ports_ref_keys:
            for port_hash in Helpers.find_by_key(exposed_port, "ExposedPorts"):
                node_inst_name = next(iter(port_hash.get("ExposedPorts")))
                link_keys = self.get_exposed_port_node_instance_links(
                    port_name, node_inst_name
                )
                flow_container_link_keys.extend(link_keys)

        # Get Links
        node_ref_keys = self.get_port_node_instance_links(port_name)

        # Join all keys
        reference_keys = [
            *node_ref_keys,
            *flow_container_link_keys,
            *exposed_ports_ref_keys,
        ]

        return reference_keys

    def get_exposed_port_node_instance_links(
        self, port_name, exposed_port_node_inst_name
    ):

        # Loop through Flows with Containers instances and get Links to the port that is exposed
        flow_container_link_keys = []
        flows_with_containers = MovaiDB().get({"Flow": {"*": {"Container": "*"}}})

        from dal.scopes.flow import Flow

        for (flow_name, flows_containers) in flows_with_containers.get("Flow").items():
            for container_node_inst_name in flows_containers.get("Container").keys():

                # Confirm that the port is from the correct Node
                container_flow_name = (
                    flows_containers.get("Container", {})
                    .get(container_node_inst_name, {})
                    .get("ContainerFlow", None)
                )

                try:
                    if self.name not in Flow(container_flow_name).ExposedPorts.keys():
                        continue
                except Exception:
                    # flow does not exist; probably a reference to a flow in the archive
                    continue

                prefix = container_node_inst_name
                node_inst_name = "{}__{}".format(prefix, exposed_port_node_inst_name)

                flow_links = MovaiDB().get({"Flow": {flow_name: {"Links": "*"}}})
                for key, value in (
                    flow_links.get("Flow", {})
                    .get(flow_name, {})
                    .get("Links", {})
                    .items()
                ):

                    if re.search(
                        r"^{0}/{1}/.+$".format(node_inst_name, port_name),
                        value.get("From"),
                    ):
                        dict_key = {"Flow": {flow_name: {"Links": {key: value}}}}
                        flow_container_link_keys.append(dict_key)

                    if re.search(
                        r"^{0}/{1}/.+$".format(node_inst_name, port_name),
                        value.get("To"),
                    ):
                        dict_key = {"Flow": {flow_name: {"Links": {key: value}}}}
                        flow_container_link_keys.append(dict_key)

        return flow_container_link_keys
