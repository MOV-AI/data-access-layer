"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva  (manuel.silva@mov.ai) - 2020
"""

from movai_core_shared.logger import Log
from movai_core_shared.consts import (ROS1_NODELETCLIENT,
                                      ROS1_NODELETSERVER,
                                      ROS1_PLUGINCLIENT,
                                      ROS1_PLUGINSERVER,
                                      MOVAI_TRANSITIONFOR,
                                      MOVAI_TRANSITIONTO)
from dal.validation import Template


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

        self.flow = flow
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

    def forced_remap(self, link: Template) -> str:
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

    def reverse_type(self, port_type : str) -> str :
        
        if port_type == "From":
            return "To"
        
        return "From" 

    def check_forced_links(self, port_type: str, link: Template) -> str:
        
        wanted_type =self.reverse_type(port_type)

        if wanted_type == "To":
            edge = link.To
        else:
            edge = link.From
        port_name = edge.str
        
        port = self.graph[port_name]

        for link_id in port["links"]:
            link_in_force_remaps = self.forced_remap(self.flow.Links[link_id])
            if link_in_force_remaps:
                return link_in_force_remaps
        return None

    def iterate_through_links(self, port_type, links: list) -> list:
        unremappable_nodes = set()
        for link_id in links:
            a = self.forced_remap(self.flow.Links[link_id])            
            forced_link = self.check_forced_links(port_type, self.flow.Links[link_id])
            if self.check_forced_links(port_type, self.flow.Links[link_id]):
                from_port = self.flow.Links[link_id].From
                to_port = self.flow.Links[link_id].To

                remap_from = self.flow.get_node_inst(from_port.node_inst).is_remappable
                remap_to = self.flow.get_node_inst(to_port.node_inst).is_remappable

                if not remap_from:
                    unremappable_nodes.add(from_port.node_inst)
                if not remap_to:
                    unremappable_nodes.add(to_port.node_inst)

        return unremappable_nodes

    def get_adjacent_unremappable_port(self, port_type, links: list) :
        unremappable_nodes = []

        for link_id in links:
            a = self.forced_remap(self.flow.Links[link_id])            
            forced_link = self.check_forced_links(port_type, self.flow.Links[link_id])
            if self.check_forced_links(port_type, self.flow.Links[link_id]):
                from_port = self.flow.Links[link_id].From
                to_port = self.flow.Links[link_id].To

                remap_from = self.flow.get_node_inst(from_port.node_inst).is_remappable
                remap_to = self.flow.get_node_inst(to_port.node_inst).is_remappable

                if not remap_from:
                    str_a = (from_port.port_name)
                    str_b = (self.flow.NodeInst[from_port.node_inst].get_params()["_namespace"])
                    str_c = str_b + "/" +str_a
                    unremappable_nodes.append(str_c)
                if not remap_to:
                    self.logger.error(to_port)
                    unremappable_nodes.append(to_port.node_inst)

        if unremappable_nodes:
            return unremappable_nodes[0]
        return None

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

            # If any port(in links) was previously remapped we must use that value but
            # if port was already remapped with a different value raise an exception
            ports_already_remapped = 0
            if port["remap"] is not None:
                ports_already_remapped += 1
               

            # First we need to check if any connected port was previously remapped
            for link in port["links"]:

                j = self.flow.Links[link].To.str.split("/")
                k = '/'.join(j[1:-1])
                
                if not self.flow.get_node_inst(self.flow.Links[link].From.node_inst).is_remappable and not self.flow.get_node_inst(self.flow.Links[link].To.node_inst).is_remappable and self.check_ros_port(self.flow.Links[link].To.node_inst, k):
                    raise Exception(f"Two non remappable nodes are connected: {self.flow.Links[link].To.str} and {self.flow.Links[link].From.str}")
                # does these port's links have a 
                port_to_remap = links[link]["To"] if port["_type"] == "From" else links[link]["From"]

                if self.graph[port_to_remap]["remap"] is not None:
                    # A second port previously remapped with a different value was found.
                    if ports_already_remapped > 0 and self.graph[port_to_remap]["remap"] != remap_to:
                        unremappable_nodes = self.iterate_through_links(port["_type"], port['links'])
                        if len(unremappable_nodes) > 1:
                            self.logger.error("Flow validator report:\nBad remap pattern detected. The following non-remappable nodes were detected in the same scope (not directly linked):\n - "+ ",\n - ".join(unremappable_nodes) + "\nLeading to the following calculated remaps (topics): \n - "+ ",\n - ".join([self.graph[port_to_remap]['remap'], remap_to]) )
                            raise Exception("Flow validation failed. Flow stopped")
                        # #TODO compare if both nodes associated with these remap ports are non-remappable
                        link_in_forced_remap = self.forced_remap(self.flow.Links[link])
                        if link_in_forced_remap:
                            remap_to = link_in_forced_remap
                            port["remap"] = remap_to
                            ports_already_remapped += 1
                            break
                        else:
                            forced_link = self.check_forced_links(port["_type"], self.flow.Links[link])
                            if forced_link:
                                remap_to = forced_link
                                port["remap"] = remap_to
                                ports_already_remapped += 1
                                break

                            else:
                                port_of_unremapable_if_exists = self.get_adjacent_unremappable_port(port['_type'], port['links'])
                                if port_of_unremapable_if_exists:
                                    remap_to = port_of_unremapable_if_exists
                                    port["remap"] = remap_to
                                    ports_already_remapped += 1
                                    break

                                else:
                                    self.logger.info(f"find {remap_to} in {self.graph}")                                  
                                    error_msg = f"Remap could not be solved. More than one port previously " \
                                                f"remapped with different values. port: {port_to_remap}"
                                    raise Exception(error_msg)

                    remap_to = self.graph[port_to_remap]["remap"]
                    port["remap"] = remap_to
                    ports_already_remapped += 1

            # Do the remap
            for link in port["links"]:
                # remap the other port
                port_to_remap = links[link]["To"] if port["_type"] == "From" else links[link]["From"]
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

        for port_name, port in self.graph.items():
            if port["remap"] not in remaps:
                remaps[port["remap"]] = {"From": [], "To": []}

            #remaps[port["remap"]].setdefault({"From": [], "To": []})

            remaps[port["remap"]][port["_type"]].append(port_name)
            
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

    def check_ros_port(self, node_name: str, port_name: str) :
        """
        function that verifies if a specific port name has a ROS message associated
            Args:
                node_name (str): simplified node name (e.g. publisher2)
                
                port_name (str): full port name (e.g. publisher2/bool_out/out)
                
                flow (Flow): Current flow being analysed where the node received is in
            
            Returns:
                bool: True if port name has a ROS message associateds. False otherwise
        """
        node_c = self.flow.full.NodeInst[node_name].node_template
        return node_c.PortsInst[port_name].Template.startswith("ROS")
