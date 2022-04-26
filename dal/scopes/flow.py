"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""
import ast
import os
import re
import uuid
from itertools import product
from dal.helpers import flatten
from movai_core_shared.consts import (
    CONFIG_REGEX,
    LINK_REGEX,
    MOVAI_STATE,
    ROS1_NODELET,
    ROS1_NODELETCLIENT,
    ROS1_NODELETSERVER,
    ROS1_PLUGIN,
    ROS1_PLUGINCLIENT,
    ROS1_PLUGINSERVER,
    ROS2_LIFECYCLENODE,
    TRANSITION_TYPE,
    MOVAI_TRANSITIONFOR,
    MOVAI_TRANSITIONTO,
)
from dal.movaidb import MovaiDB
from .scope import Scope
from .ports import Ports
from .node import Node
from ..models.var import Var
from movai_core_shared.exceptions import DoesNotExist
from .configuration import Configuration
from movai_core_shared.logger import Log

LOGGER = Log.get_logger("Flow")


class Flow(Scope):
    """Flow class"""

    scope = "Flow"

    def __init__(self, name, version="latest", new=False, db="global"):
        super().__init__(scope="Flow", name=name, version=version, new=new, db=db)
        self.__dict__["cache_calc_remaps"] = None
        self.__dict__["cache_dict"] = None
        self.__dict__["cache_node_insts"] = {}
        self.__dict__["cache_node_templates"] = {}
        self.__dict__["cache_ports_templates"] = {}
        self.__dict__["cache_node_params"] = {}
        self.__dict__["cache_container_params"] = {}

        # cache parent flow parameters
        # to override when getting parameters of a node in a subflow
        self.__dict__["parent_parameters"] = {}

    # ported
    def expand_container(self, label: str, flow: str, prev_flows: list) -> dict:
        """Returns the Links and Nodes in a Flow container with namespace"""
        container = {}
        if flow in prev_flows:
            raise Exception("Flow already in use, this will lead to infinite recursion")
        flow_dict = Flow(flow).get_dict(prev_flows=prev_flows, recursive=True)

        container["Links"] = {}
        for link, value in flow_dict["Flow"][flow]["Links"].items():
            if value["From"] != "start/start/start":
                value["From"] = "%s__%s" % (label, value["From"])
            value["To"] = "%s__%s" % (label, value["To"])
            container["Links"].update({"%s__%s" % (label, link): value})

        container["NodeInst"] = {}
        for node, value in flow_dict["Flow"][flow]["NodeInst"].items():
            value["NodeLabel"] = "%s__%s" % (label, value.get("NodeLabel", node))
            container["NodeInst"].update({"%s__%s" % (label, node): value})

        return container

    # ported
    def get_dict(self, prev_flows=None, recursive=False):
        """Get full structure of flow including containers expanded"""
        temp_dict = super().get_dict()
        if recursive:
            if not prev_flows:
                prev_flows = []
            prev_flows.append(self.name)
            for container in temp_dict["Flow"][self.name].get("Container", {}):
                prev_flows_copy = prev_flows.copy()
                flow = temp_dict["Flow"][self.name]["Container"][container][
                    "ContainerFlow"
                ]
                label = temp_dict["Flow"][self.name]["Container"][container][
                    "ContainerLabel"
                ]
                container = self.expand_container(label, flow, prev_flows_copy)
                temp_dict["Flow"][self.name].setdefault("Links", {}).update(
                    container.get("Links", {})
                )
                temp_dict["Flow"][self.name].setdefault("NodeInst", {}).update(
                    container.get("NodeInst", {})
                )

        return temp_dict

    # NOT PORTED -> Links
    def is_valid(self, new_link: dict = None) -> tuple:
        """Calculate remaps and validate links"""

        dict_ports = {}  # { "From/To" : "Link name", ...}

        if self.__dict__["cache_dict"] is None:
            self.__dict__["cache_dict"] = self.get_dict(recursive=False)

        links = self.cache_dict["Flow"][self.name].get("Links", {})
        # TODO: validate new_link
        if new_link is not None:
            links.update(new_link)

        # {"From": "", "To": "", "Error": True or False}
        for link_name, link in links.items():
            # create link with format "From/To"
            str_fromto = "%s/%s" % (link["From"], link["To"])
            # add "From/To": "Link"
            dict_ports[str_fromto] = link_name

        # remaps = {} # { "remap": {"To": ["port_name,..."], "From": ["port_name,..."]} }
        remaps = self.calc_remaps(new_link)

        # VALIDATE LINKS
        # iterate through all remaps
        # recreate links with the format From/To
        # check if the link exists in dict_ports constructed earlier
        result = []  # list of dicts {'from': str, 'to': str, 'valid': bool}

        for _key, remap in remaps.items():
            for f_entity, t_entity in product(remap["From"], remap["To"]):
                str_link = "%s/%s" % (f_entity, t_entity)
                is_valid = True if str_link in dict_ports else False
                link = {"from": f_entity, "to": t_entity, "valid": is_valid}
                result.append(link)

        return (all(map(lambda value: value["valid"], result)), result)

    # ported -> flow.remaps (property)
    def calc_remaps(self, new_link: dict = None) -> dict:
        """
        Calculate remaps
        data: {"port_name": { "remap": None, "links": ["link_name",...], "Type": "From" or "To"}}
        """
        if self.__dict__["cache_calc_remaps"] is not None:
            return self.__dict__["cache_calc_remaps"]

        data = {}
        if self.__dict__["cache_dict"] is None:
            self.__dict__["cache_dict"] = self.get_dict(recursive=True)
        links = self.cache_dict["Flow"][self.name].get("Links", {})
        # TODO: validate new_link
        if new_link is not None:
            links.update(new_link)

        for link, value in links.items():  # {"From": "", "To": ""}
            if (
                "START/START/START" in value["From"].upper()
                or "START/START/START" in value["To"].upper()
            ):
                continue
            if (
                "END/END/END" in value["From"].upper()
                or "END/END/END" in value["To"].upper()
            ):
                continue
            # ignore nodelets links
            types_to_skip = [
                ROS1_PLUGINCLIENT,
                ROS1_PLUGINSERVER,
                ROS1_NODELETCLIENT,
                ROS1_NODELETSERVER,
                MOVAI_TRANSITIONFOR,
                MOVAI_TRANSITIONTO,
            ]

            p_from = re.findall(LINK_REGEX, value["From"])
            node_inst_from, _, port_name_from, _, _ = p_from[0]
            p_to = re.findall(LINK_REGEX, value["To"])
            node_inst_to, _, port_name_to, _, _ = p_to[0]
            if (
                self.get_node_port_template(node_inst_from, port_name_from)
                in types_to_skip
                or self.get_node_port_template(node_inst_to, port_name_to)
                in types_to_skip
            ):

                continue

            data_port_from = data.get(
                value["From"], {"type": "From", "remap": None, "count": 0, "links": []}
            )
            data_port_from["count"] += 1
            data_port_from["links"].append(link)
            # node_inst = value["From"].split("/")[0]

            if self.is_node_dummy(node_inst_from) or not self.is_node_remmapable(
                node_inst_from
            ):
                namespace = self.get_node_namespace(node_inst_from)
                if namespace:
                    data_port_from["remap"] = "%s/%s" % (namespace, port_name_from)
                else:
                    data_port_from["remap"] = port_name_from
            data[value["From"]] = data_port_from

            data_port_to = data.get(
                value["To"], {"type": "To", "remap": None, "count": 0, "links": []}
            )
            data_port_to["count"] += 1
            data_port_to["links"].append(link)
            if self.is_node_dummy(node_inst_to) or not self.is_node_remmapable(
                node_inst_to
            ):
                namespace = self.get_node_namespace(node_inst_to)
                if namespace:
                    data_port_from["remap"] = "%s/%s" % (namespace, port_name_to)
                else:
                    data_port_from["remap"] = port_name_to
            data[value["To"]] = data_port_to

        # list of ports sorted by count (nr. of connections)
        ports = sorted(data, key=lambda key: data[key]["count"])
        while ports:
            port_name = ports.pop()
            port = data[port_name]

            # port was already remapped ? remap to port["remap"] otherwise to port name.
            remap_to = port["remap"] or port_name

            # If any port(in links) was previously remapped we must use that value but
            # if port was already remapped with a different value raise an exception
            ports_already_remapped = 0
            if port["remap"] is not None:
                ports_already_remapped += 1

            # First we need to check if any connected port was previously remapped
            for link in port["links"]:
                port_to_remap = (
                    links[link]["To"] if port["type"] == "From" else links[link]["From"]
                )
                if data[port_to_remap]["remap"] is not None:
                    # A second port previously remapped with a different value was found.
                    if (
                        ports_already_remapped > 0
                        and data[port_to_remap]["remap"] != remap_to
                    ):
                        error_msg = (
                            f"Remap could not be solved. More than one port previously "
                            f"remapped with different values. port: {port_to_remap}"
                        )
                        raise Exception(error_msg)

                    remap_to = data[port_to_remap]["remap"]
                    port["remap"] = remap_to
                    ports_already_remapped += 1

            # Do the remap
            for link in port["links"]:
                # remap the other port
                port_to_remap = (
                    links[link]["To"] if port["type"] == "From" else links[link]["From"]
                )
                data[port_to_remap]["remap"] = remap_to

        # collect remaps to a dictionary
        # { "remap": {"To": ["port_name,..."], "From": ["port_name,..."]} }
        remaps = {}
        for port_name in data:
            port = data[port_name]
            if port["remap"] not in remaps:
                remaps[port["remap"]] = {"From": [], "To": []}
            remaps[port["remap"]][port["type"]].append(port_name)
        self.__dict__["cache_calc_remaps"] = remaps
        return remaps

    # ported
    def get_start_nodes(self) -> list:
        """List of nodes with a start port"""
        output = []
        if self.__dict__["cache_dict"] is None:
            self.__dict__["cache_dict"] = self.get_dict(recursive=True)
        for _link_name, link in (
            self.cache_dict["Flow"][self.name].get("Links", {}).items()
        ):
            port_from = link["From"]
            port_to = link["To"]
            if "START/START/START" in port_from.upper():
                node_inst = port_to.split("/")[0]
                output.append(node_inst)
        return output

    # ported -> flow
    def get_lifecycle_nodes(self) -> list:
        """List of Ros2 Lifecycle Nodes"""
        if self.__dict__["cache_dict"] is None:
            self.__dict__["cache_dict"] = self.get_dict(recursive=True)
        all_node_inst = self.cache_dict["Flow"][self.name].get("NodeInst", {})
        output = []
        for node_inst in all_node_inst:
            if self.get_node_type(node_inst) == ROS2_LIFECYCLENODE:
                output.append(node_inst)
        return output

    # WONT PORT -> NodeInst
    # node_inst = flow.get_node_inst(<node_inst name>)["ref"]
    # node_inst.dependencies (property)
    # ported -> flow.get_node_dependencies
    def get_node_dependencies(
        self,
        node_name: str,
        dependencies_collected: list = None,
        links_to_skip: list = None,
        skip_parent_node: str = None,
        first_level_only: bool = False,
    ) -> list:
        """Get node dependencies recursively"""

        dependencies = []

        if dependencies_collected is not None:
            dependencies += dependencies_collected

        if links_to_skip is None:
            links_to_skip = []

        # do not include node_name as a dependency
        if skip_parent_node is None:
            skip_parent_node = set()
        skip_parent_node.add(node_name)

        node_transitions = self.get_node_transitions(node_name)

        if self.__dict__["cache_dict"] is None:
            self.__dict__["cache_dict"] = self.get_dict(recursive=True)

        links = self.cache_dict["Flow"][self.name].get("Links", {})

        for link_name in links:
            if link_name in links_to_skip:
                continue

            port_from = links[link_name]["From"]
            port_to = links[link_name]["To"]

            # link dependencies level
            # 0: check dependencies in both directions (From and To)
            # 1: check dependencies only From -> To
            # 2: check dependencies only To -> From
            # 3: do not check dependencies
            dependencies_level = links[link_name].get("Dependency", 0)
            dependencies_level = (
                dependencies_level if (3 >= dependencies_level >= 0) else 0
            )

            # do not check link dependencies
            if dependencies_level == 3:
                continue

            dependencies_from_to = dependencies_level in (0, 1)
            dependencies_to_from = dependencies_level in (0, 2)

            dependency_name = None
            # start is not a dependency
            if (
                "START/START/START" in port_from.upper()
                or "END/END/END" in port_to.upper()
            ):
                links_to_skip.append(link_name)
                continue

            if node_name == port_from.split("/")[0] and dependencies_from_to:
                dependency_name = port_to.split("/")[0]
            if node_name == port_to.split("/")[0] and dependencies_to_from:
                dependency_name = port_from.split("/")[0]

            if dependency_name is not None and dependency_name not in skip_parent_node:
                # transition nodes are not considered as dependencies
                if dependency_name in node_transitions:
                    continue
                if self.get_node_type(dependency_name) == MOVAI_STATE:
                    continue
                if dependency_name not in dependencies:
                    # skip link prevents never ending recursion
                    links_to_skip.append(link_name)
                    dependencies.append(dependency_name)
                    if not first_level_only:
                        dependencies = self.get_node_dependencies(
                            dependency_name,
                            dependencies,
                            links_to_skip,
                            skip_parent_node,
                        )

        return list(set(dependencies))

    # ported -> Flow.get_node_plugins
    def get_node_plugins(self, node_name: str) -> list:
        """Return NodeInst(s) of type ROS1_PLUGIN linked to node_name"""
        output = []
        # get first level node dependencies
        dependencies = self.get_node_dependencies(
            node_name=node_name, first_level_only=True
        )
        for dependency in dependencies:
            if self.get_node_type(dependency) == ROS1_PLUGIN:
                output.append(dependency)
        return output

    # WONT PORT -> use Node directly
    # node_inst = flow.get_node_inst(<node_inst name>)["ref"]
    # node_template = node_inst.node_template
    # envvars = node_template.EnvVar
    # port part of the code to the flowmonitor (related w the type)
    def get_node_attributes(
        self, node_name: str, attr: str, only_values: bool = False
    ) -> dict:
        """ "Generic method to get node attributes"""
        output = {}
        if self.__dict__["cache_dict"] is None:
            self.__dict__["cache_dict"] = self.get_dict(recursive=True)
        node_inst = self.cache_dict["Flow"][self.name]["NodeInst"][node_name]
        node_template = self.get_node(node_name)

        for param, value in node_template.get(attr, {}).items():
            # NodeInst Parameter overrides default parameter
            if param in node_inst.get(attr, {}):
                value = node_inst[attr][param]

            if only_values:
                output.update({param: value["Value"]})
            else:
                if node_template.get("Type", None) == ROS1_PLUGIN:
                    plugin_name = node_template["Path"].split("/")[-1]
                    output.update(
                        {param: "_%s/%s:=%s" % (plugin_name, param, value["Value"])}
                    )
                else:
                    output.update({param: "%s:=%s" % (param, value["Value"])})

        return output

    # ported -> use NodeInst.params
    # node_inst = flow.get_node_inst(<node_inst name>)
    # node_inst.params
    def get_node_inst_params(self, node_name: str, attribute="Parameter") -> dict:
        """Returns the parameters changed in the node intance"""

        if self.__dict__["cache_dict"] is None:
            self.__dict__["cache_dict"] = self.get_dict(recursive=True)
        params = self.cache_dict["Flow"][self.name]["NodeInst"][node_name].get(
            attribute, {}
        )
        return {key: value["Value"] for key, value in params.items()}

    # ported -> NodeInst.params (property)
    def get_node_params(self, node_name: str) -> dict:
        """Returns the final parameters of the node instance"""
        params = self.__dict__["cache_node_params"].get(node_name, None)

        if not params:
            params = {}

            params_raw = self.get_node(node_name).get("Parameter", {})
            output = {key: value["Value"] for key, value in params_raw.items()}

            output.update(self.get_node_inst_params(node_name))

            # Parameters are saved as strings so they need to be evaluated into its original type
            for key, value in output.items():
                try:
                    params[key] = ast.literal_eval(value)
                except:
                    # If literal eval failed we check if the String has references
                    try:
                        params[key] = self.parse_param(
                            output[key], output, node_name, key
                        )
                    except:
                        # In older versions params were not stored as Strings
                        LOGGER.warning(
                            "Parameter %s of node %s is not saved correctly!"
                            % (key, node_name)
                        )
                        params[key] = output[key]
            self.__dict__["cache_node_params"].update({node_name: params})

        return params

    # ported -> ParamParser
    def eval_reference(
        self, param_value: str, node_name: str, full_params: dict, param_name: str
    ):
        """
        Returns the parameter value. If the value is a valid expression, it is evaluated.

        Parameters:
            param_value (str): the parameter value/expression  $(context reference)
            node_name (str): the node instance name
            full_params (dict): dictionary with all the node instance parameters
            param_name (str): the name of the parameter

        Returns:
            output (str): the parameter value after evaluation
        """
        output = param_value

        mapping = {
            "config": self.eval_config,
            "param": self.eval_param,
            "var": self.eval_var,
            "flow": self.eval_flow,
        }

        try:
            # $(<context> <parameter reference>)
            # ex.: $(flow var_A)
            pattern = re.compile(r"\$\((.*)\s(.*)\)")
            result = pattern.search(param_value)

            output = mapping.get(result.group(1))(
                result.group(2), param_value, node_name, full_params, param_name
            )

        except Exception as error:
            msg = f"error evaluating {param_value}; {error}"
            LOGGER.error(msg)

        return str(output)

    # ported -> ParamParser
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

        output = Configuration(_config_name, db=self.db).get_param(_config_param)

        return output

    # ported -> ParamParser
    def eval_param(
        self, param_ref: str, param: str, node_name: str, full_params: dict, *__
    ) -> any:
        """
        Returns the param expression evaluated
            ex.: $(param name)

        Parameters:
            param_ref (str): reference to a parameter
            param (str): parameter expression   $(<context> <parameter reference>)
                ex.: $(param var_A)
            node_name (str): node name (ignored)
            full_params (dict): dictionary with all the parameters

        Returns:
            output (any): the expression evaluated
        """

        output = full_params.get(param_ref, param)

        return output

    # ported -> ParamParser
    def eval_var(self, reference: str, *__) -> any:
        """
        Returns the var expression evaluated
            ex.: $(var robot.name)

            Parameters:
                reference (str): reference to a parameter  <fleet or robot>.<parameter reference>

            Returns:
                output (any): the expression evaluated
        """

        context, param_name, *__ = reference.split(".")
        output = Var(context).get(param_name)

        if not output:
            raise Exception(f'"{param_name}" does not exist in Var "{context}"')

        return output

    # ported -> ParamParser
    def eval_flow(
        self,
        reference: str,
        param: str,
        node_name: str,
        full_params: dict,
        param_name: str,
        *__,
    ) -> any:
        """
        Evaluate the flow expression ex.: $(flow myvar)

            Parameters:
                reference (str): reference to a parameter
                    ex.: "var_A"
                param (str): parameter expression  $(<context> <parameter reference>)
                    ex.: $(flow var_A)
                node_name (str): the name of the name
                full_params (dict): dictionary with all the parameters
                param_name (str): the parameter name

            Returns:
                output (any): the parameter value after evaluation
        """

        output = None

        # if node is inside a sub flow the name will be subflow2__subflow1__node
        node_name_arr = node_name.split("__")

        try:
            if len(node_name_arr) > 1:
                # get the value from the container parameter or sub-flow
                curr_flow = self

                counter = 0
                while counter < len(node_name_arr):
                    name = node_name_arr[counter]

                    if counter != len(node_name_arr) - 1:  # it is a container
                        output = curr_flow.get_container_params(name)

                        # get the container flow (sub flow)
                        curr_flow = Flow(curr_flow.Container.get(name).ContainerFlow)

                        # pass current container parameters to the sub flow
                        curr_flow.__dict__["parent_parameters"].update(output)

                    else:  # it is a node
                        output = curr_flow.get_node_params(name).get(param_name, None)

                    counter += 1

            else:
                # get the value from the flow parameter
                flow_params = {
                    key: value.Value for key, value in self.Parameter.items()
                }

                # override the parameters with the parent flow parameters previously set
                flow_params.update(self.__dict__["parent_parameters"])

                output = flow_params.get(reference)

            if not output:
                raise Exception

        except:

            # get the value from the node template
            output = (
                self.get_node(node_name)
                .get("Parameter", {})
                .get(reference, {})
                .get("Value")
            )

        if not output:
            raise Exception(f'"{reference}" is not a valid flow parameter')

        return output

    # NOT PORTED -> Container.params (property)
    def get_container_params(self, node_name: str) -> dict:
        """
        Returns the container parameters after evaluating them

            Parameters:
                node_name (str): the container name

            Returns:
                params (dict): the container parameters after evaluating them

        """
        params = self.__dict__["cache_container_params"].get(node_name, None)

        if not params:

            container = self.Container.get(node_name)

            params = {}

            try:
                # get the parameter from the container parameters
                _params = {
                    key: value.Value for key, value in container.Parameter.items()
                }

                # Parameters are saved as strings so they need to be evaluated into its original type
                for key, value in _params.items():
                    try:
                        params[key] = ast.literal_eval(value)
                    except:
                        # If literal eval failed we check if the String has references
                        try:
                            params[key] = self.parse_param(
                                _params[key], _params, node_name, key
                            )
                        except:
                            # In older versions params were not stored as Strings
                            LOGGER.warning(
                                "Parameter %s of node %s is not saved correctly!"
                                % (key, node_name)
                            )
                            params[key] = _params[key]

                self.__dict__["cache_container_params"].update({node_name: params})

            except Exception as error:
                LOGGER.error(error)

        return params

    # ported -> ParamParser
    def parse_param(self, param: str, full_params: dict, node_name: str, key: str):
        """Check if the parameter has a reference to a config, param or env var"""

        param = os.path.expandvars(param)
        while 1:
            temp_param = param
            param = re.sub(
                CONFIG_REGEX,
                lambda m: self.eval_reference(m.group(), node_name, full_params, key),
                param,
            )

            if param == temp_param:
                try:
                    return ast.literal_eval(param)
                except:
                    return param

    # ported -> flow.get_node_transitions
    def get_node_transitions(self, node_name: str, port: str = None) -> list:
        """Returns node to transit to"""
        transition_nodes = set()
        for link_value, _, port_type in self.get_node_ports_gen(node_name, port):
            if (
                port_type["Protocol"] == TRANSITION_TYPE["Protocol"]
                and port_type["Transport"] == TRANSITION_TYPE["Transport"]
            ):
                transition_nodes.add(link_value.split("/")[0])
        return list(transition_nodes)

    # ported -> NodeInst.Template
    def get_node_template_name(self, node_inst_name: str) -> str:
        """Returns the template of a node inst"""
        template_name = self.cache_node_insts.get(node_inst_name)
        if not template_name:
            if self.__dict__["cache_dict"] is None:
                self.__dict__["cache_dict"] = self.get_dict(recursive=True)
            template_name = self.cache_dict["Flow"][self.name]["NodeInst"][
                node_inst_name
            ]["Template"]
            self.cache_node_insts.update({node_inst_name: template_name})
        return template_name

    # ported -> NodeInst.node_template (instance of Node)
    def get_node(self, node_inst_name: str) -> dict:
        """Return the node dict from cache or from DB"""
        template_name = self.get_node_template_name(node_inst_name)

        node_template = self.cache_node_templates.get(template_name)
        if not node_template:
            node_template = MovaiDB(db=self.db).get({"Node": {template_name: "**"}})[
                "Node"
            ][template_name]
            self.cache_node_templates.update({template_name: node_template})

        return node_template

    # ported - Node.get_port(<port template>)
    def get_port(self, port_template: str) -> dict:
        """Return ports dict from cache or from DB"""
        ports = self.cache_ports_templates.get(port_template)
        if not ports:
            ports = MovaiDB(db=self.db).get({"Ports": {port_template: "**"}})["Ports"][
                port_template
            ]
            self.cache_ports_templates.update({port_template: ports})
        return ports

    # ported - Node.Path
    # node_inst = flow.get_node_inst(<node_inst name>)["ref"]
    # node_template = nodes_inst.node_template()
    # node_template.Path
    def get_node_path(self, node_name: str) -> str:
        """Return node type"""
        return self.get_node(node_name).get("Path", None)

    # ported - Node.Type
    # node_inst = flow.get_node_inst(<node_inst name>)["ref"]
    # node_template = nodes_inst.node_template()
    # node_template.Type
    def get_node_type(self, node_name: str) -> str:
        """Return node type"""
        return self.get_node(node_name).get("Type", None)

    # ported -> NodeInst.is_persistent (property)
    def get_node_persistent(self, node_name: str) -> bool:
        """Return node persistance"""
        if self.__dict__["cache_dict"] is None:
            self.__dict__["cache_dict"] = self.get_dict(recursive=True)
        persist = self.cache_dict["Flow"][self.name]["NodeInst"][node_name].get(
            "Persistent"
        )
        if persist is not None:
            return persist
        return self.get_node(node_name).get("Persistent", None)

    # ported -> flow.get_nodelet_manager
    def get_nodelet_manager(self, node_name: str, port: str = None) -> str:
        """Returns nodelet manager name"""
        if self.get_node_type(node_name) == ROS1_NODELET:
            for link_value, port_template, _ in self.get_node_ports_gen(
                node_name, port
            ):
                if port_template == ROS1_NODELETCLIENT:
                    return link_value.split("/")[0]
        return None

    # WONT PORT -> Node
    def get_node_ports_gen(self, node_name: str, port: str = None):
        """
        [Generator] Returns ports node links
        'port' must be PortInst/port_name
        """
        node_template = self.get_node(node_name)
        regex = "^%s/.*/.*" % node_name
        if port is not None:
            regex = "^%s/%s/" % (node_name, port)

        if self.__dict__["cache_dict"] is None:
            self.__dict__["cache_dict"] = self.get_dict(recursive=True)

        links = self.cache_dict["Flow"][self.name].get("Links", {})

        for _key, value in links.items():
            if re.findall(
                regex,
                value["From"],
            ):
                p = re.findall(LINK_REGEX, value["From"])
                _node_inst, _, port_inst, _, port_name = p[0]
                link_value = value["To"]
                port_type_name = "Out"
            elif re.findall(regex, value["To"]):
                p = re.findall(LINK_REGEX, value["To"])
                _node_inst, _, port_inst, _, port_name = p[0]
                link_value = value["From"]
                port_type_name = "In"
            else:
                continue
            port_template_name = node_template["PortsInst"][port_inst]["Template"]

            port = self.get_port(port_template_name)
            port_type = port[port_type_name][port_name]

            # CHANGE -> port_template was a Ports() class, now its the name
            # port_template = Ports(port_template_name, db=self.db)
            port_template = port_template_name

            yield (link_value, port_template, port_type)

    # WONT PORT - Node
    def get_node_port_template(self, node_name: str, port_inst: str) -> str:
        """Returns the name of the template for that specific portsinst"""
        node_template = self.get_node(node_name)
        port_template_name = node_template["PortsInst"][port_inst]["Template"]
        return port_template_name

    # WONT PORT
    def get_node_port(self, node_name: str, port_inst: str) -> Ports:
        """Deprecated, still here because of tests/data/test_Callback_data.py"""
        node_template_name = self.get_node_template_name(node_name)
        node_template = Node(node_template_name, db=self.db)
        port_template_name = node_template.PortsInst[port_inst].Template
        return Ports(port_template_name, db=self.db)

    # ported -> NodeInst
    def is_node_dummy(self, node_name: str) -> bool:
        """Return node dummy"""
        if self.__dict__["cache_dict"] is None:
            self.__dict__["cache_dict"] = self.get_dict(recursive=True)
        dummy_inst = self.cache_dict["Flow"][self.name]["NodeInst"][node_name].get(
            "Dummy"
        )
        if dummy_inst is not None:
            return dummy_inst
        return self.get_node(node_name).get("Dummy", False)

    # ported -> NodeInst
    def is_node_remmapable(self, node_name: str) -> bool:
        """Return node remappable, True if not defined"""
        if not self.get_node_params(node_name).get("_remappable", True):
            print("Node inst %s is not remappable" % node_name)
            return False
        return True

    # ported -> NodeInst
    def get_node_namespace(self, node_name: str) -> str:
        """Return node namespace, '' if not defined"""
        return self.get_node_params(node_name).get("_namespace", "")

    # ported -> NodeInst
    def is_node_to_launch(self, node_name: str) -> bool:
        """Return node launch, True if not defined"""
        if not self.get_node_params(node_name).get("_launch", True):
            print("Node inst %s is not to launch" % node_name)
            return False
        return True

    # NOT PORTED
    def __getTemplate(self, key: str, name: str) -> str:
        """returns the template name (NodeInst) or flow name (Container)
        Args:
            key: NodeInst or Container
            name: instance name

        Return:
            template name or None
        """
        template_keys = {"NodeInst": "Template", "Container": "ContainerFlow"}

        try:
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

        except AttributeError as error:
            LOGGER.error(error)

    # NOT PORTED
    def delete(self, key: str, name: str):
        """Delete object dependencies"""

        template = self.__getTemplate(key, name)

        try:
            result = super().delete(key, name)

            # delete NodeInst or Container Links
            if result > 0 and key in ["NodeInst", "Container"]:

                # string to check will be nodeInst1/nodeInst2
                # name can be nodeInst or nodeInst__otherName
                pattern = f"^{name}/.+|^{name}__.*/|/{name}$|/{name}__.*$"

                for link, value in self.Links.items():
                    # split From and To by / to get the nodeInst
                    # expected format is nodeInst/portInst/portName
                    values = [
                        prop.split("/", 1)[0] for prop in [value["From"], value["To"]]
                    ]

                    # join the values into one string
                    # if pattern found delete link
                    if re.findall(pattern, "/".join(values)):
                        del self.Links[link]

                exposed_ports_dict = self.ExposedPorts.get(template, None)
                # delete node exposed ports
                if self.delete_exposed_port(template, "*", name):
                    # we want to delete links only if there was exposed ports.
                    if exposed_ports_dict:
                        for port in exposed_ports_dict.get(name, []):
                            self.delete_exposed_port_links(name, port)

        except Exception as error:
            LOGGER.error(str(error))
            return False

        return True

    # ported -> Links.add

    def add_link(
        self,
        source_node: str,
        source_port: str,
        target_node: str,
        target_port: str,
        source_type: str = "",
        target_type: str = "",
    ) -> tuple:
        """Verifies if the links already exists if not add it to the Links hash"""

        src_separator = "__" if source_type == "MovAI/Flow" else "/"
        trg_separator = "__" if target_type == "MovAI/Flow" else "/"

        source = src_separator.join([source_node, source_port])
        target = trg_separator.join([target_node, target_port])

        new_link = {"From": source, "To": target}

        # check if link already exists
        for _, link in self.Links.items():
            if new_link == link:
                # link already exists -> return empty tuple
                return ()

        _db_write = MovaiDB(db=self.db).db_write

        # Generate new ID
        _id = str(uuid.uuid4())
        self.Links.update({_id: new_link})

        return _id, new_link

    # ported -> Links.delete
    def delete_link(self, link_id: str) -> bool:
        """Delete link"""
        LOGGER.info("{}".format(link_id))
        try:
            self.Links.delete(link_id)
            LOGGER.info("Link deleted {}".format(link_id))
            return True
        except Exception as e:
            LOGGER.error(str(e))
            return False

    # NOT PORTED -> Links move it to class Nodeinst
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
                self.ExposedPorts.delete(node_id)

            return True

        except DoesNotExist:
            # No exposed ports...
            pass

        except Exception as e:
            LOGGER.error(str(e))

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
        # Container: {"ContainerFlow": <Flow name>, "ContainerLabel": <container name>}
        flows_with_containers = flows or MovaiDB(db=self.db).get(
            {"Flow": {"*": {"Container": "*"}}}
        )

        # Loop flows that have subflows
        for flow_name, flow_containers in flows_with_containers.get("Flow", {}).items():

            # Loop throught subflows
            for flow_container in next(iter(flow_containers.values())).values():

                # check if the subflow is referencing me
                if flow_container.get("ContainerFlow", "") == self.name:

                    try:

                        container_label = flow_container.get("ContainerLabel", "")
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
                        regex = rf"{_port_prefix}__{node_inst_name}{_join_char}{port_name}/.+"

                        # the flow where the ContainerFlow is
                        flow = Flow(flow_name)
                        flow_links = {**flow.Links}

                        # delete the link associated with the port
                        for link_id, link in flow_links.items():
                            _to = link.get("To")
                            _from = link.get("From")
                            if re.match(regex, _to) or re.match(regex, _from):
                                flow.Links.delete(link_id)

                        # delete the exposed port
                        flow_exposed_ports = {**flow.ExposedPorts}

                        # __<Flow name> is how we identify flows in the exposed ports
                        if f"__{self.name}" in flow_exposed_ports.keys():

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
                        LOGGER.error(str(e))

        return True

    # NOT PORTED -NodeInst?
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

    # ported - NodeInst.copy()
    def copy_node(
        self,
        copy_name: str,
        org_name: str,
        org_flow: str,
        org_type: str = "NodeInst",
        options: dict = None,
    ):
        """copy a node instance"""

        labels = {"NodeInst": "NodeLabel", "Container": "ContainerLabel"}

        try:
            _flow = self if org_flow == self.name else type(self)(org_flow)

            node_to_copy = getattr(_flow, org_type)[org_name]
            new_node = node_to_copy.get_dict()
            new_node[labels[org_type]] = copy_name

            if options:
                new_node.update(options)

            MovaiDB(db=self.db).set(
                {
                    self.__class__.__name__: {
                        self.name: {org_type: {copy_name: new_node}}
                    }
                }
            )

        except Exception as error:
            return False, repr(error)
        else:
            return True, None

    # ported -> flow.on_flow_delete (not static)

    @staticmethod
    def on_flow_delete(flow_id: str):
        """
        Actions to do when a flow is deleted
        - Delete all nodes of type Container with ContainerFlow = flow_id
        """

        for flow_name in Flow.get_all():
            flow = Flow(flow_name)
            for c_name, c_value in flow.Container.items():
                if c_value.ContainerFlow == flow_id:
                    flow.delete("Container", c_name)
