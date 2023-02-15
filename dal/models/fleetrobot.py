"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Erez Zomer  (erez@mov.ai) - 2023
"""
from .model import Model
from .scopestree import scopes


class FleetRobot(Model):
    """
    A FleetRobot Model
    """
    @staticmethod
    def get_robot_pub_key_by_name(robot_name: str) -> str:
        """Returns the public key of a robot by the robot name.

        Args:
            robot_name (str): The name of the robot to get his public key.

        Returns:
            str: The public key.
        """
        for robot in scopes().list_scopes(scope="Robot"):
            fleet_robot = scopes.from_path(robot["url"])
            if fleet_robot.RobotName == robot_name:
                return fleet_robot.PublicKey
        return ""

    @staticmethod
    def get_robot_pub_key_by_ip(robot_ip: str) -> str:
        """Returns the private key of a robot by the robot name.

        Args:
            robot_ip (str): The ip address of the robot to get his public key.

        Returns:
            str: The public key.
        """
        for robot in scopes().list_scopes(scope="Robot"):
            fleet_robot = scopes.from_path(robot["url"])
            if fleet_robot.IP == robot_ip:
                return fleet_robot.PublicKey
        return ""

    @staticmethod
    def get_robot_id_by_ip(robot_ip: str) -> str:
        """Returns the robot id of a robot by the robot ip address.

        Args:
            robot_ip (str): The ip address of the robot to get his public key.

        Returns:
            str: The robot's id.
        """
        for robot in scopes().list_scopes(scope="Robot"):
            fleet_robot = scopes.from_path(robot["url"])
            if fleet_robot.IP == robot_ip:
                return fleet_robot.ID
        return ""

# Register FleetRobot class as a model
Model.register_model_class("Robot", FleetRobot)
