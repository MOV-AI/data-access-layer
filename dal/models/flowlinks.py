"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
import re
import uuid
from .scopestree import ScopePropertyNode, ScopeNode
from dal.validation import Template


class FlowLinks(ScopePropertyNode):
    """
    A link in the flow
    """

    __LINK_CONFIG_TEMPLATE__ = {
        "node_inst": str,
        "port_name": str,
        "port_type": str,
        "str": str,
    }

    __LINK_TEMPLATE__ = {
        "From": __LINK_CONFIG_TEMPLATE__,
        "To": __LINK_CONFIG_TEMPLATE__,
        "Dependency": int,
    }

    __DEFAULT_DEPENDENCY__ = 0

    LINK_REGEX = r"^([~@a-zA-Z_0-9-]+)([\/])([\/~@a-zA-Z_0-9]+)+([\/])([~@a-zA-Z_0-9]+)$"

    def __init__(self, name: str, value: str):
        super().__init__(name, value)
        self.cache = {}

    def __getitem__(self, key: str) -> Template:
        data = None

        try:
            # request link from the list of links in the main flow (without prefix)
            data = self.value[key]

        except KeyError:
            # request the link from the list of all links in the flow and subflows (with prefix)
            data = self.full[key]

        return Template.load_dict(FlowLinks._parse_link(data), FlowLinks.__LINK_TEMPLATE__)

    @property
    def flow(self):
        """Returns an instance (Flow) of the flow"""
        return self.parent

    @staticmethod
    def _parse_link(link: dict) -> dict:
        """Parse a link into a dictionary
        Parameters:
            link (dict): the link to parse
                {
                    {"From": "<node inst>/<port name>/<port type>"},
                    {"To": "<node inst>/<port name>/<port type>"}
                }
        Returns:
            output (dict): the link parsed
            {
                {"From": {"node_inst": str, "port_name": str, "port_type": str, "str": str},
                "To": {"node_inst": str, "port_name": str, "port_type": str, "str": str},
                "Dependency": int}
            }
        """
        output = {}
        try:
            for direction in ["From", "To"]:
                # split <node inst>/<port name 1><port name n>/<port type>
                node_inst, _, port_name, _, port_type = re.findall(
                    FlowLinks.LINK_REGEX, link[direction]
                )[0]

                output[direction] = {
                    "node_inst": node_inst,
                    "port_name": port_name,
                    "port_type": port_type,
                    "str": link[direction],
                }

            dep_level = link.get("Dependency", 0)
            output["Dependency"] = dep_level if (3 >= dep_level >= 0) else 0

        except Exception as error:
            raise ValueError("Invalid link format: %s" % link[direction]) from error

        return output

    def get_link(self, key: str) -> Template:
        """
        Return link by ID  (only main flow)
        """
        return Template.load_dict(
            FlowLinks._parse_link(self.value[key]), FlowLinks.__LINK_TEMPLATE__
        )

    def count(self) -> int:
        """
        Return number of links (only main flow)
        """
        return len(self.value)

    def ids(self) -> list:
        """
        Return ids of the links in the main flow
        """
        return self.value.keys()

    def items(self) -> dict:
        """
        return link data
        """
        return self.value.items()

    @property
    def full(self) -> dict:
        """
        Return all links in the flow and subflows
        """
        return self.flow.full.Links

    def _is_valid(self):
        pass

    def add(
        self,
        source_node: str,
        source_port: str,
        target_node: str,
        target_port: str,
        source_type: str = "",
        target_type: str = "",
    ) -> tuple:
        """
        Add a new link
        """

        # TODO review returns
        # TODO test

        if self.flow.workspace != "global":
            return ()

        src_separator = "__" if source_type == "MovAI/Flow" else "/"
        trg_separator = "__" if target_type == "MovAI/Flow" else "/"

        source = src_separator.join([source_node, source_port, source_type])
        target = trg_separator.join([target_node, target_port, target_type])

        new_link = {"From": source, "To": target}

        # check if link already exists
        for _, link in self.items():
            if new_link == link:
                # link already exists -> return empty tuple
                return ()

        # Generate new ID
        _id = str(uuid.uuid4())

        self.value.update({_id: new_link})

        return _id, new_link

    def delete(self, link_id: str) -> bool:
        """
        Delete a new link in the main flow
        """

        # TODO test

        try:
            del self.value[link_id]
            return True

        except KeyError:
            return False

    def get_node_links(self, node_name: str) -> list:
        """Returns the node instance links in the flow and subflows"""
        if node_name in self.cache:
            return self.cache[node_name]
        links = []

        for key in self.full:
            link = self.flow.Links[key]

            if node_name in [link.From.node_inst, link.To.node_inst]:
                _type = "From" if node_name == link.From.node_inst else "To"
                _link = {"Type": _type, "ref": link, "id": key}

                links.append(_link)
        self.cache[node_name] = links
        return links


ScopeNode.register_scope_property("schemas/1.0/Flow/Links", FlowLinks)
