"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020

   Module that implements Robot namespace
"""
import uuid
import pickle
from movai_core_shared.exceptions import DoesNotExist
from .scope import Scope
from dal.movaidb import MovaiDB
from .fleetrobot import FleetRobot
from .configuration import Configuration


class Robot(Scope):
    """Robot class that deals with robot related stuff"""

    scope = "Robot"

    def __init__(self):

        robot_struct = MovaiDB("local").search_by_args("Robot", Name="*")[0]

        if robot_struct:
            for name in robot_struct["Robot"]:
                super().__init__(
                    scope="Robot", name=name, version="latest", new=False, db="local"
                )
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
            # copy all data to the global

    def set_ip(self, ip_address: str):
        """Set the IP Adress of the Robot"""
        self.IP = ip_address
        self.fleet.IP = ip_address

    def set_name(self, name: str):
        """Set the Name of the Robot"""
        self.RobotName = name
        self.fleet.RobotName = name

    def send_cmd(self, command, *, flow=None, node=None, port=None, data=None) -> None:
        """Send an action command to the Robot"""
        to_send = {}
        for key, value in locals().items():
            if value is not None and key in ("command", "flow", "node", "port", "data"):
                to_send.update({key: value})

        to_send = pickle.dumps(to_send)

        self.Actions.append(to_send)

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
