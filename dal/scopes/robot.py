"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020

   Module that implements Robot namespace
"""
from typing import Optional
import asyncio
import uuid
import pickle

from movai_core_shared.core.message_client import MessageClient, AsyncMessageClient
from movai_core_shared.exceptions import DoesNotExist
from movai_core_shared.consts import COMMAND_HANDLER_MSG_TYPE, TIMEOUT_SEND_CMD_RESPONSE
from movai_core_shared.envvars import SPAWNER_BIND_ADDR, DEVICE_NAME

from dal.scopes.scope import Scope
from dal.movaidb import MovaiDB
from dal.scopes.fleetrobot import FleetRobot
from .configuration import Configuration


class Robot(Scope):
    """Robot class that deals with robot related stuff

    You should also read the page :doc:`/robot_parameters` for a deep dive on the Parameters feature.
    """

    spawner_client: MessageClient
    async_spawner_client: AsyncMessageClient

    scope = "Robot"

    def __init__(self):
        robot_struct = MovaiDB("local").search_by_args("Robot", Name="*")[0]

        if robot_struct:
            for name in robot_struct["Robot"]:
                super().__init__(scope="Robot", name=name, version="latest", new=False, db="local")
                try:
                    self.__dict__["fleet"] = FleetRobot(name)
                    self.RobotName = self.fleet.RobotName
                except DoesNotExist:
                    self.__dict__["fleet"] = FleetRobot(name, new=True)
                    self.fleet.RobotName = self.RobotName
                break  # only first is used if more exist (by some dark magic)

        else:  # no robot exists so lets init one
            unique_id = uuid.uuid4()
            # print(unique_id.hex)
            super().__init__(
                scope="Robot",
                name=unique_id.hex,
                version="latest",
                new=True,
                db="local",
            )
            self.RobotName = "robot_" + unique_id.hex[0:6]

            self.__dict__["fleet"] = FleetRobot(unique_id.hex, new=True)
            self.fleet.RobotName = "robot_" + unique_id.hex[0:6]
            self.RobotType = ""
            self.fleet.RobotType = ""
            self.RobotModel = ""
            self.fleet.RobotModel = ""
        # default : ipc:///opt/mov.ai/comm/SpawnerServer-{DEVICE_NAME}-{FLEET_NAME}.sock"
        server = SPAWNER_BIND_ADDR
        self.__dict__["spawner_client"] = MessageClient(server_addr=server, robot_id=self.name)
        self.__dict__["async_spawner_client"] = AsyncMessageClient(
            server_addr=server, robot_id=self.name
        )

    def set_ip(self, ip_address: str):
        """Set the IP Adress of the Robot"""
        self.IP = ip_address
        self.fleet.IP = ip_address

    def set_name(self, name: str):
        """Set the Name of the Robot"""
        self.RobotName = name
        self.fleet.RobotName = name

    def set_type(self, rType: str):
        """Set the Type of the Robot"""
        self.RobotType = rType
        self.fleet.RobotType = rType

    def set_model(self, model: str):
        """Set the Model of the Robot"""
        self.RobotModel = model
        self.fleet.RobotModel = model

    def send_cmd(self, command, *, flow=None, node=None, port=None, data=None) -> None:
        """Send an action command to the Robot

        if wait_for_status is True, we assume the Robot will return a message"""
        command_data = {}
        if command:
            command_data["command"] = command

        if flow:
            command_data["flow"] = flow

        if node:
            command_data["node"] = node

        if port:
            command_data["port"] = port

        if data:
            command_data["data"] = data

        req_data = {"command_data": command_data}

        if (
            self.RobotName == DEVICE_NAME
            and hasattr(self, "spawner_client")
            and self.spawner_client is not None
        ):
            self.spawner_client.send_request(COMMAND_HANDLER_MSG_TYPE, req_data)
        else:
            command_data = pickle.dumps(command_data)
            self.Actions.append(command_data)

    async def async_send_cmd(
        self, command, *, flow=None, node=None, port=None, data=None, wait_for_status=False
    ) -> Optional[dict]:
        """Send an action command to the Robot

        if wait_for_status is True, we assume the Robot will return a message"""
        command_data = {}
        if command:
            command_data["command"] = command

        if flow:
            command_data["flow"] = flow

        if node:
            command_data["node"] = node

        if port:
            command_data["port"] = port

        if data:
            command_data["data"] = data

        req_data = {"command_data": command_data}

        if (
            self.RobotName == DEVICE_NAME
            and hasattr(self, "spawner_client")
            and self.spawner_client is not None
        ):
            try:
                response = await asyncio.wait_for(
                    self.async_spawner_client.send_request(
                        COMMAND_HANDLER_MSG_TYPE, req_data, response_required=wait_for_status
                    ),
                    timeout=TIMEOUT_SEND_CMD_RESPONSE,
                )
                if wait_for_status:
                    return {"status": response}
            except asyncio.TimeoutError:
                return {"error": "Timeout"}
        else:
            command_data = pickle.dumps(command_data)
            self.Actions.append(command_data)

    def update_status(self, status: dict, db: str = "all"):
        """Update the Robot status in the database"""
        Robot.cls_update_status(self.name, status, db)

    def get_states(self):
        """Gets the states of the robot from its own configuration.
        When Robot groups are implemented it should merge with the group configuration"""
        try:
            states = Configuration(self.RobotName).get_param("states")
        except:
            states = {}
        return states

    def set_param(self, param: str, value, db: str = "all"):
        """Sets or updates a parameter of the robots"""
        self.Parameter[param].Value = value

    @classmethod
    def cls_update_status(cls, name: str, status: dict, db: str = "all"):
        """Class method to update the Robot status in the database
        This method reduces readings from the database compared to using Robot instance
        """

        to_send = {"Robot": {name: {"Status": status}}}
        if db in ["all", "global"]:
            MovaiDB("global").set(to_send)
        if db in ["all", "local"]:
            MovaiDB("local").set(to_send)
