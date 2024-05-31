"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva  (manuel.silva@mov.ai) - 2020
"""
from typing import TYPE_CHECKING

from movai_core_shared.logger import Log
from movai_core_shared.consts import (ROS1_NODELETCLIENT,
                                      ROS1_NODELETSERVER,
                                      ROS1_PLUGINCLIENT,
                                      ROS1_PLUGINSERVER,
                                      MOVAI_TRANSITIONFOR,
                                      MOVAI_TRANSITIONTO)
from dal.validation import Template

if TYPE_CHECKING:
    from dal.models import Flow


class GFlow:
    """
    Graph generator in use to calculate remaps
    """
    __SKIP__ = [ROS1_PLUGINCLIENT, ROS1_PLUGINSERVER,
                ROS1_NODELETCLIENT, ROS1_NODELETSERVER,
                MOVAI_TRANSITIONFOR, MOVAI_TRANSITIONTO]

    __START__ = "START/START/START"
    __END__ = "END/END/END"

    logger = Log.get_logger("gflow.mov.ai")

    def __init__(self, flow):

        self.flow: "Flow" = flow
        self.graph = {}
        self.remaps = {}

    def get_vertex(self, key: str, _type: str = "From") -> dict:
        """ Get or create a new vertex """

        init = {"_type": _type, "remap": None, "count": 0, "links": []}
        return self.graph.setdefault(key, init)

    def add_edge(self, key: str, _id: str, _type: str) -> dict:
        """ Add a new edge to the vertex """

        vertex = self.get_vertex(key, _type)
        vertex["links"].append(_id)

        return vertex

    def set_remap(self, key: str, remap: str):
        """ Set the vertex remap value """

        self.get_vertex(key)["remap"] = remap

    def forced_remap(self, link) -> str:
        """ Special remap rules """

        output = None

        for vertex in [link.From, link.To]:

            name = vertex.node_inst

            # get the node instance
            node_inst = self.flow.get_node_inst(name)

            remappable = node_inst.is_remappable
            dummy = node_inst.is_dummy

            namespace = self.flow.get_node_inst_param(name, "_namespace")

            if dummy or not remappable:
                output = f"{namespace}/{vertex.port_name}" if namespace else vertex.port_name

        return output

    def should_skip(self, link: Template) -> bool:
        """ Special rules for including vertex in the graph """

        ports = set([GFlow.__START__, GFlow.__END__])

        link_values = [link.From.str.upper(), link.To.str.upper()]

        # skip if port is __START__ or __END__
        if any(value in ports for value in link_values):
            return True

        # for value in link.values():  Template class does not have .values
        for value in [link.From, link.To]:

            try:
                # check if the port type should be skipped
                if self.get_port_template(value.node_inst, value.port_name) in GFlow.__SKIP__:
                    return True
            except AttributeError:
                msg = f"Invalid link found in {self.flow.ref}.\
                     From: {link.From.str}  To: {link.To.str}"
                self.logger.error(msg)
                return True

        return False

    def generate_graph(self) -> dict:
        """ Generate the graph """

        # initialize the graph
        self.graph = {}

        # iterate over all th links in the main flow and subflows
        for link_id in self.flow.Links.full.keys():

            link = self.flow.Links[link_id]

            if self.should_skip(link):
                continue

            self.add_edge(link.From.str, link_id, "From")
            self.add_edge(link.To.str, link_id, "To")

            forced_remap = self.forced_remap(link)
            if forced_remap:
                self.set_remap(link.From.str, forced_remap)

        return self.graph

    def generate_remaps(self) -> dict:
        """ Generates the remaps """

        if not self.graph:
            self.generate_graph()

        # list of ports sorted by count (nr. of connections)
        ports = self.sort_graph()

        links = self.flow.Links.full

        # TODO review and refactor
        while ports:
            port_name = ports.pop()
            port = self.graph[port_name]

            # port was already remapped ? remap to port["remap"] otherwise to port name.
            remap_to = port["remap"] or port_name
            if remap_to in self.graph:
                remap_to_type = self.graph[remap_to]["_type"]
            else:
                remap_to_type = "From" if port["_type"] == "To" else "To"

            # If any port(in links) was previously remapped we must use that value but
            # if port was already remapped with a different value raise an exception
            ports_already_remapped = 0
            if port["remap"] is not None:
                ports_already_remapped += 1

            # First we need to check if any connected port was previously remapped
            for link in port["links"]:
                port_to_remap = links[link]["To"] if port["_type"] == "From" else links[link]["From"]

                if self.graph[port_to_remap]["remap"] is not None:

                    # A second port previously remapped with a different value was found.
                    if ports_already_remapped > 0 and self.graph[port_to_remap]["remap"] != remap_to:
                        error_msg = f"Remap could not be solved. More than one port previously " \
                                    f"remapped with different values. port: {port_to_remap}"
                        raise Exception(error_msg)

                    remap_to = self.graph[port_to_remap]["remap"]
                    port["remap"] = remap_to
                    ports_already_remapped += 1

            # Do the remap
            for link in port["links"]:
                port_to_remap = links[link]["To"] if port["_type"] == "From" else links[link]["From"]

                # Don't remap to ports that don't exist
                if remap_to not in self.graph:
                    self.logger.warning("Port %s is not in graph!", remap_to)
                    continue

                # Only remap ports To-From or From-To, not of the same type
                if port_to_remap != remap_to and port["_type"] != remap_to_type:
                    self.logger.warning("Can't remap %s to %s!", port_to_remap, remap_to)
                    continue

                # remap the other port
                self.graph[port_to_remap]["remap"] = remap_to

        return self.graph

    def calc_remaps(self) -> dict:
        """
        Returns the remaps after calculation
        """

        self.generate_graph()
        self.generate_remaps()

        # convert graph
        remaps = {}

        for _id, port in self.graph.items():

            if port["remap"] not in remaps:
                remaps[port["remap"]] = {"From": [], "To": []}

            #remaps[port["remap"]].setdefault({"From": [], "To": []})

            remaps[port["remap"]][port["_type"]].append(_id)

        # cache remaps
        self.remaps = remaps

        return self.remaps

    def get_remaps(self, force: bool = False) -> dict:
        """ Returns the calculated remaps """

        # return cached remaps
        if self.remaps and not force:
            return self.remaps

        return self.calc_remaps()

    def sort_graph(self) -> list:
        """ Sort the graph by the number of elements in links """
        data = sorted(self.graph, key=lambda key: len(
            self.graph[key]["links"]))

        return data

    def get_port_template(self, node_inst: str, port_name: str) -> str:
        """ Get the port template from the node template """

        # get Node instance
        node_template = self.flow.get_node_inst(node_inst).node_template

        return node_template.PortsInst[port_name].Template
