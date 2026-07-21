"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Message Model
"""

# pylint: disable=invalid-name
from collections import deque
from typing import Dict
import genmsg
import rosmsg

from .scopestree import scopes
from dal.scopes.system import System
from .model import Model

from movai_core_shared.logger import Log


logger = Log.get_logger(__name__)


class Message(Model):
    """Message Model implementation

    use Deprecated one instead
    """

    # default __init__

    def is_valid(self):
        """Returns True"""
        return True

    @staticmethod
    def get_portdata(db="local") -> System:
        """
        Retrieve or initialize the PortsData object from the specified database.

        If the PortsData entry does not exist, it will be created.

        Args:
            db (str): The database identifier to connect to (default is "local").

        Returns:
            Dict: The PortsData system object.
        """
        try:
            ports_data = System("PortsData", db=db)
        except Exception as e:
            logger.info("PortsData not found initializing...: %s", e)
            ports_data = System("PortsData", new=True, db=db)
        return ports_data

    @staticmethod
    def fetch_portdata_api() -> Dict:
        """
        Fetch the stored PortsData value for API usage.

        Returns:
            Dict: The value stored in the PortsData object.
        """
        return Message.get_portdata().Value

    @staticmethod
    def update_portdata(new_data: Dict):
        """
        Update the PortsData value with new package data.

        Existing keys will be overwritten, and new keys will be added.

        Args:
            new_data (Dict): A dictionary containing package types and their data.
        """
        ports_data = Message.get_portdata()

        db_data = ports_data.Value
        if db_data is None:
            db_data = {}

        for package_type in new_data.keys():
            db_data[package_type] = new_data[package_type]

        ports_data.Value = db_data

    @staticmethod
    def fetch_portdata_messages() -> Dict:
        """Get all messages and services available for callbacks"""

        portdata = Message.fetch_portdata_api()
        ret = {}
        for key in set.union(set(portdata["ROS1_msg"]), set(portdata["ROS1_srv"])):
            ret[key] = list(
                set(portdata["ROS1_msg"].get(key, []) + portdata["ROS1_srv"].get(key, []))
            )
        return ret

    @staticmethod
    def get_structure(message: str) -> Dict:
        """Gives the full structure of a message given 'package/message' input"""

        package, name = message.split("/")

        try:  # message
            return Message._parse_msg(rosmsg.get_msg_text(message))
        except rosmsg.ROSMsgException:
            # not there
            pass

        try:  # service
            return Message._parse_msg(rosmsg.get_srv_text(message))
        except rosmsg.ROSMsgException:
            # not there either
            pass

        # DB
        mobj = scopes().Message[package]
        context = genmsg.MsgContext()
        # message
        if name in mobj.Msg:
            return Message._parse_msg(
                rosmsg.spec_to_str(
                    context, rosmsg.load_msg_from_string(context, mobj.Msg[name].Source, message)
                )
            )
        elif name in mobj.Srv:
            spec = rosmsg.load_srv_from_string(context, mobj.Srv[name].Source, message)
            parts = (
                rosmsg.spec_to_str(context, spec.request),
                rosmsg.spec_to_str(context, spec.response),
            )
            return Message._parse_msg(str.join("---\n", parts))
        # else
        return {}

    @staticmethod
    def _parse_msg(text: str) -> Dict:
        if "---" in text:
            req, res = text.split("---\n")
            return {
                "srv": {
                    "request": Message._parse_part(deque(req.splitlines())),
                    "response": Message._parse_part(deque(res.splitlines())),
                }
            }
        # else
        return {"msg": Message._parse_part(deque(text.splitlines()))}

    @staticmethod
    def _parse_part(lines, _pre=""):
        _next_pre = _pre + "  "
        msg = {}
        current = None
        line = lines.popleft().rstrip()
        while line.startswith(_pre):
            if line.startswith(_next_pre):
                lines.appendleft(line)
                msg[current]["content"] = Message._parse_part(lines, _next_pre)
                try:
                    line = lines.popleft()
                    continue
                except IndexError:
                    break
            t, current = line.strip().split(" ")
            msg[current] = {"type": t}
            try:
                line = lines.popleft()
            except IndexError:
                break
        if line != "":
            lines.appendleft(line)
        return msg


Model.register_model_class("Message", Message)
