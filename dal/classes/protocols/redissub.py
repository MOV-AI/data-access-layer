"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020

   Module that implements Redis Subscriber as a GD_Node input protocol
"""
import asyncio
from typing import Any
from dal.movaidb import MovaiDB, RedisClient
from dal.scopes.robot import Robot

try:
    from gd_node.message import GD_Message
    from gd_node.protocols.base import BaseIport

    gdnode_modules = {
        "GD_Message": GD_Message,
        "BaseIport": BaseIport,
    }
except ImportError:
    gdnode_modules = {}


from gd_node.protocols.base import BaseIport


class VarSubscriber(BaseIport):

    """
    Redis Var Event Subscriber. Implementention of redis pubsub

    Args:
        _node_name: Name of the node instance
        _port_name:  Name of the port
        _topic: Iport topic - not used
        _message: Custom Message containing subscribed info
        _callback: Name of the callback to be executed
    """

    def __init__(
        self,
        _node_name: str,
        _port_name: str,
        _topic: str,
        _message: str,
        _callback: str,
        _params: dict,
        _update: bool,
        **_ignore
    ):
        """Init"""
        super().__init__(_node_name, _port_name, _topic, _message, _callback, _update)

        self.msg = gdnode_modules["GD_Message"]("movai_msgs/redis_sub").get()
        self.loop = asyncio.get_event_loop()

        scopes = ["node", "robot", "fleet", "global", "flow"]

        var_type = _params.get("Type", "Node").lower()
        var_name = _params.get("Variable", "")

        if var_type not in scopes:
            raise Exception(
                "'" + var_type + "' is not a valid scope. Choose between: " + str(scopes)[1:-1]
            )

        prefixes = {
            "node": _node_name + "@",
            "robot": "@",
            "fleet": Robot().name + "@",
            "global": "@",
            "flow": "flow@",
        }

        prefix = prefixes.get(var_type, "@")

        self.db = "global" if var_type in ("fleet", "global") else "local"

        sub_dict = {"Var": {var_type: {"ID": {prefix + var_name: {"Value": ""}}}}}

        self.loop.create_task(self.register_sub(self.db, self.loop, sub_dict, self.callback))

    async def register_sub(self, db, loop, sub_dict, callback):
        """Register the subscriber"""
        databases = await RedisClient.get_client()
        await MovaiDB(db=db, loop=loop, databases=databases).subscribe(sub_dict, callback)

    def callback(self, msg: Any) -> None:
        """Callback of the Redis subscriber protocol

        Args:
            msg: Redis psubscribe message
        """
        new_msg = self.msg()

        operation = msg[1]
        new_msg.type = operation
        changed_key = msg[0].decode("utf-8").split(":", 1)
        changed_dict = MovaiDB(self.db).keys_to_dict([(changed_key[1], "")])

        if operation == "del":
            new_msg.data = None
        elif operation == "set":
            new_msg.data = MovaiDB(self.db).get_value(changed_dict)

        super().callback(new_msg)
