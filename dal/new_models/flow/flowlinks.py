"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2023
   - Erez Zomer (erez@mov.ai) - 2023
"""
import re
from typing import ClassVar, Optional
import uuid

from pydantic import ConfigDict, BaseModel, field_validator


DEFAULT_DEPENDENCY = 0
LINK_REGEX = r"^([~@a-zA-Z_0-9-]+)([\/])([\/~@a-zA-Z_0-9]+)+([\/])([~@a-zA-Z_0-9]+)$"
regex = re.compile(LINK_REGEX)


class LinkConfigTemplate(BaseModel):
    """A class that implements LinkConfigTemplate field."""

    node_inst: str
    port_name: str
    port_type: str
    str: str


class FlowLink(BaseModel):
    """A class that implements FlowLink field."""

    From: LinkConfigTemplate
    To: LinkConfigTemplate
    Dependency: int = DEFAULT_DEPENDENCY
    __DEFAULT_DEPENDENCY__: ClassVar[int] = DEFAULT_DEPENDENCY

    @field_validator("From", "To", mode="before")
    @classmethod
    def validate_regex(cls, value, field):
        if isinstance(value, dict):
            return value
        try:
            l = value.split("/")
            node_inst, port_name, port_type = l[0], "/".join(l[1 : len(l) - 1]), l[-1]
            output = {
                "node_inst": node_inst,
                "port_name": port_name,
                "port_type": port_type,
                "str": value,
            }

            return output
        except Exception as e:
            raise ValueError(
                f"Field {field.alias} with value {value} does not match the required pattern {LINK_REGEX}., Exception {e}"
            )

    model_config = ConfigDict(exclude={"__DEFAULT_DEPENDENCY__"}, extra="allow")

    def model_dump(self):
        return {"From": self.From.str, "To": self.To.str, "Dependency": self.Dependency}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parser = None

    @property
    def full(self) -> dict:
        """Returns the data from the main flow and all subflows"""

        return self._parser.flow.full.Links

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
                node_inst, _, port_name, _, port_type = re.findall(LINK_REGEX, link[direction])[0]

                output[direction] = {
                    "node_inst": node_inst,
                    "port_name": port_name,
                    "port_type": port_type,
                    "str": link[direction],
                }

            dep_level = link.get("Dependency", 0)
            output["Dependency"] = dep_level if (3 >= dep_level >= 0) else 0

        except Exception as error:
            raise ValueError("Invalid link format") from error

        return output

    '''
    def get_link(self, key: str) -> Template:
        """
        Return link by ID  (only main flow)
        """
        return Template.load_dict(
            FlowLinks._parse_link(self.value[key]), FlowLinks.__LINK_TEMPLATE__
        )
    '''

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

        src_separator = "__" if source_type == "MovAI/Flow" else "/"
        trg_separator = "__" if target_type == "MovAI/Flow" else "/"

        source = src_separator.join([source_node, source_port])
        target = trg_separator.join([target_node, target_port])

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
