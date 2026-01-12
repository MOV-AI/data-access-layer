"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
   - Dor Marcous (dor@mov.ai) - 2022

   Module that implements Robot namespace
"""
import pickle
from typing import Dict, List, Optional
from enum import Enum

from movai_core_shared.common.utils import is_enterprise
from movai_core_shared.core.message_client import MessageClient, AsyncMessageClient
from movai_core_shared.consts import COMMAND_HANDLER_MSG_TYPE
from movai_core_shared.envvars import (
    DEVICE_NAME,
    SPAWNER_BIND_ADDR,
    MESSAGE_SERVER_PORT,
)
from movai_core_shared.exceptions import RobotRunning
from movai_core_shared.logger import Log


from dal.movaidb import MovaiDB

from .scope import Scope

logger = Log.get_logger("FleetRobot")

ROBOT_STARTED_PARAM = "started"
START_TIME_VAR = "startTime"
END_TIME_VAR = "endTime"


class Role(Enum):
    """Robot Role Enum."""

    MANAGER = "manager"
    MEMBER = "member"


class FleetRobot(Scope):
    """Represent the Robot scope in the redis-master."""

    spawner_client: MessageClient
    async_spawner_client: AsyncMessageClient
    Parameter: Dict

    def __init__(self, name: str, version="latest", new=False, db="global"):
        """constructor

        Args:
            name (str): The name which the robot is represented in db (the robot_id in this case)
            version (str, optional): the verison of the object.. Defaults to "latest".
            new (bool, optional): if true creates a new object. Defaults to False.
            db (str, optional): "global/local". Defaults to "global".
        """
        super().__init__(scope="Robot", name=name, version=version, new=new, db=db)
        if self.RobotName == DEVICE_NAME or not is_enterprise():
            # default : ipc:///opt/mov.ai/comm/SpawnerServer-{DEVICE_NAME}-{FLEET_NAME}.sock"
            server = SPAWNER_BIND_ADDR
        else:
            # Message needs to be sent to the message-server
            # which will be forwarded to the spawner server of the remote robot {self.IP}
            server = f"tcp://message-server:{MESSAGE_SERVER_PORT}"

        self.__dict__["spawner_client"] = MessageClient(server_addr=server, robot_id=self.RobotName)
        self.__dict__["async_spawner_client"] = AsyncMessageClient(
            server_addr=server, robot_id=self.RobotName
        )

    def send_cmd(
        self, command: str, *, flow: str = None, node: str = None, port=None, data=None
    ) -> None:
        """Send an action command to the Robot.

        See flow-initiator/flow_initiator/spawner/spawner.py for possible commands.

        """
        dst = {"ip": self.IP, "host": self.RobotName, "id": self.name}

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

        req_data = {"dst": dst, "command_data": command_data}

        # For retro-compatibility, if the dest robot is a fleet robot
        # then the response is required since the forward by message-server might fail
        # in this case, the command will be published to redis
        send_to_redis = False
        response_required = False
        if self.RobotName != DEVICE_NAME and is_enterprise():
            logger.debug("%s is a fleet member", self.RobotName)
            response_required = True

        if hasattr(self, "spawner_client") and self.spawner_client is not None:
            res = self.spawner_client.send_request(
                COMMAND_HANDLER_MSG_TYPE, req_data, response_required=response_required
            )
            if (not response_required) or (
                response_required
                and res is not None
                and "response" in res
                and res["response"] != {}
            ):
                # success if response is not required or if required, is well formed
                logger.info("Sent command %s to robot %s", command_data, self.RobotName)
            else:
                logger.debug(
                    "Failed to send command %s %s, response: %s", command_data, self.RobotName, res
                )
                send_to_redis = True
        else:
            logger.debug("Spawner client not found for %s", self.RobotName)
            send_to_redis = True

        if send_to_redis:
            logger.info("Command %s, published in redis for robot %s", command_data, self.RobotName)
            command_data = pickle.dumps(command_data)
            self.Actions.append(command_data)

    async def async_send_cmd(
        self,
        command: str,
        *,
        flow: str = None,
        node: str = None,
        port=None,
        data=None,
        response_required=False,
    ) -> None:
        """Send an action command to the Robot.

        See flow-initiator/flow_initiator/spawner/spawner.py for possible commands.

        """
        dst = {"ip": self.IP, "host": self.RobotName, "id": self.name}

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

        req_data = {"dst": dst, "command_data": command_data}

        # For retro-compatibility, if the dest robot is a fleet robot
        # then the response is required since the forward by message-server might fail
        # in this case, the command will be published to redis
        send_to_redis = False
        if self.RobotName != DEVICE_NAME and is_enterprise():
            logger.debug("%s is a fleet member", self.RobotName)
            response_required = True

        if hasattr(self, "async_spawner_client") and self.async_spawner_client is not None:
            res = await self.async_spawner_client.send_request(
                COMMAND_HANDLER_MSG_TYPE, req_data, response_required=response_required
            )
            if not response_required:
                # success if response is not required or if required, is well formed
                logger.info("Sent command %s to robot %s", command_data, self.RobotName)
            elif res is not None and "response" in res and res["response"] != {}:
                # success if response is not required or if required, is well formed
                logger.info("Sent command %s to robot %s", command_data, self.RobotName)
                return res["response"]
            else:
                logger.debug(
                    "Failed to send command %s %s, response: %s", command_data, self.RobotName, res
                )
                send_to_redis = True
        else:
            logger.debug("Spawner client not found for %s", self.RobotName)
            send_to_redis = True

        if send_to_redis:
            logger.info("Command %s, published in redis for robot %s", command_data, self.RobotName)
            command_data = pickle.dumps(command_data)
            self.Actions.append(command_data)

    @staticmethod
    def get_robot_key_by_ip(ip_address: str, key_name: str) -> Optional[bytes]:
        """Finds a key of a robot by the ip address.

        Args:
            ip_address (str): The ip address of the desired robot.
            key_name (str): The name of required key.

        Returns:
            bytes: The public key.
        """
        robo_keys = {"IP": "", "PublicKey": ""}
        db = MovaiDB("global")
        fleet_robots = db.search_by_args("Robot", Name="*")[0]["Robot"]
        for robot_id in fleet_robots:
            robo_dict = {"Robot": {robot_id: robo_keys}}
            robot = db.get(robo_dict)["Robot"][robot_id]
            if robot["IP"] == ip_address:
                return robot[key_name]
        return None

    def set_robot_started(self, value: bool):
        try:
            self.Parameter[ROBOT_STARTED_PARAM].Value = value
        except Exception as e:
            logger.warning(
                f"Caught exception in setting {ROBOT_STARTED_PARAM} Parameter with value {value} of robot id {id}",
                e,
            )
            self.add("Parameter", ROBOT_STARTED_PARAM).Value = value

    def ping(self) -> bool:
        """Ping the robot"""

        req_data = {
            "dst": {"ip": self.IP, "host": self.RobotName, "id": self.name},
            "command_data": {
                "command": "PING",
            },
        }

        res = self.spawner_client.send_request(
            COMMAND_HANDLER_MSG_TYPE, req_data, response_required=True
        )
        return res is not None and "response" in res and res["response"] != {}

    @staticmethod
    def list_all() -> List[str]:
        """List all the robots in the fleet"""

        db = MovaiDB("global")
        all_robots_data = db.search_by_args("Robot")[0]
        return list(all_robots_data["Robot"].keys())

    @classmethod
    def remove_entry(cls, robot_id: str, force: bool = False):
        """Remove the robot from the registry

        robot_id: str
            the id of the robot to remove

        force: bool
            if True, the robot will be removed without checking if it is running
            if not, an exception will be raised if the robot is running
        """

        robot = cls(robot_id)
        if robot.is_manager():
            raise ValueError("Cannot remove the manager robot")
        if not force and robot.ping():
            raise RobotRunning(
                f"Robot {robot_id} is running. Use force=True if you stil want to remove it"
            )

        db = MovaiDB("global")
        all_robots_data = db.search_by_args("Robot")[0]
        robot_to_remove = {"Robot": {robot_id: all_robots_data["Robot"][robot_id]}}
        deleted_count = db.delete(robot_to_remove)
        return deleted_count is not None and deleted_count > 0

    @staticmethod
    def name_to_id(robot_name: str) -> str:
        """Get the robot id by its name.

        Args:
            robot_name: Robot name.

        Returns:
            Robot id.

        """
        db = MovaiDB("global")
        all_robots_data = db.search_by_args("Robot")[0]
        for robot_id, robot_data in all_robots_data["Robot"].items():
            if robot_data["RobotName"] == robot_name:
                return robot_id

   @staticmethod
    def id_to_name(robot_id: str) -> str:
        """Get the robot name by its id.
        Args:
            robot_id: Robot id.
        Returns:
            Robot name.
        """
        db = MovaiDB("global")
        all_robots_data = db.search_by_args("Robot")[0]
        for _robot_id, robot_data in all_robots_data["Robot"].items():
            if _robot_id == robot_id:
                return robot_data["RobotName"]
               
    def is_manager(self) -> bool:
        """Check if the Robot is a manager

        Returns:
            bool: True if the Robot is a manager, False otherwise.

        """
        return self.Role == Role.MANAGER.value

    @classmethod
    def get_members(cls) -> List[str]:
        """Get a list with the members ids.

        Returns:
            List[str]: List of member robot ids.

        """
        db = MovaiDB("global")
        robots = db.search_by_args("Robot")[0]

        members = []

        if "Robot" not in robots:
            return members

        for robot_id in robots["Robot"]:
            if FleetRobot(robot_id).Role == Role.MEMBER.value:
                members.append(robot_id)

        return members

    @classmethod
    def get_manager(cls) -> Optional[str]:
        """Get the manager id.

        Returns:
            Optional[str]: The manager robot id or None if not found.

        """
        db = MovaiDB("global")
        robots = db.search_by_args("Robot")[0]

        if "Robot" not in robots:
            return None

        for robot_id in robots["Robot"]:
            if FleetRobot(robot_id).Role == Role.MANAGER.value:
                return robot_id
        return None
