"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Ofer Katz (ofer@mov.ai) - 2022
"""

import os
from dal.movaidb import MovaiDB


class LocalRobotInfo:
    """
    Helper class for retrieving the robot id  and robot name from the local Redis DB
    """
    robot_id = None
    robot_name = None

    @staticmethod
    def get_id():
        """
        Returns the robot ID
        """
        if LocalRobotInfo.robot_id is None:
            LocalRobotInfo._get_robot_info()

        return LocalRobotInfo.robot_id

    @staticmethod
    def get_name():
        """
        Returns the robot name
        """
        if LocalRobotInfo.robot_name is None:
            LocalRobotInfo._get_robot_info()

        return LocalRobotInfo.robot_name

    @staticmethod
    def _get_robot_info():
        """
        Fetch from the local Redis DB the robot ID and robot name
        """
        robot_struct = MovaiDB("local").search_by_args("Robot", Name="*")[0]
        if robot_struct:
            for name in robot_struct["Robot"]:
                LocalRobotInfo.robot_id = name
                LocalRobotInfo.robot_name = robot_struct["Robot"][name].get('RobotName')
        else:
            LocalRobotInfo.robot_id = ''
            LocalRobotInfo.robot_name = os.getenv('DEVICE_NAME')
