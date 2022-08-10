"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Ofer Katz (ofer@mov.ai) - 2022
"""

import os
from dal.movaidb import MovaiDB


class RobotInfo:
    robot_id = None
    robot_name = None

    @staticmethod
    def get_id():
        if RobotInfo.robot_id is None:
            RobotInfo._get_robot_info()

        return RobotInfo.robot_id

    @staticmethod
    def get_name():
        if RobotInfo.robot_name is None:
            RobotInfo._get_robot_info()

        return RobotInfo.robot_name

    @staticmethod
    def _get_robot_info():
        robot_struct = MovaiDB("local").search_by_args("Robot", Name="*")[0]
        if robot_struct:
            for name in robot_struct["Robot"]:
                RobotInfo.robot_id = name
                RobotInfo.robot_name = robot_struct["Robot"][name].get('RobotName')
        else:
            RobotInfo.robot_id = ''
            RobotInfo.robot_name = os.getenv('DEVICE_NAME')
