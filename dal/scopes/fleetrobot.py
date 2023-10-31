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

from movai_core_shared.common.utils import is_enteprise, is_manager
from movai_core_shared.consts import COMMAND_HANDLER_MSG_TYPE
from movai_core_shared.envvars import MOVAI_FLOW_PORT, MESSAGE_SERVER_LOCAL_ADDR
from movai_core_shared.logger import Log
from movai_core_shared.core.message_client import MessageClient

from dal.movaidb import MovaiDB

from .scope import Scope

logger = Log.get_logger("FleetRobot")


class FleetRobot(Scope):
    """Represent the Robot scope in the redis-master.
    """

    def __init__(self, name: str, version="latest", new=False, db="global"):
        """constructor

        Args:
            name (str): The name which the robot is represented in db (the robot_id in this case)
            version (str, optional): the verison of the object.. Defaults to "latest".
            new (bool, optional): if true creates a new object. Defaults to False.
            db (str, optional): "global/local". Defaults to "global".
        """
        super().__init__(scope="Robot", name=name, version=version, new=new, db=db)
        if is_enteprise():
            server = MESSAGE_SERVER_LOCAL_ADDR
        else:
            server = f"tcp://spawner:{MOVAI_FLOW_PORT}"
        self.message_client = MessageClient(server_addr=server,robot_id=self.RobotName)

    def send_cmd(self, command, *, flow=None, node=None, port=None, data=None) -> None:
        """Send an action command to the Robot"""
        dst = {
            "IP": self.IP,
            "HOST": self.RobotName,
            "ID": self.name
        }
        request = {
            "dst": dst
        }
        for key, value in locals().items():
            if value is not None and key in ("command", "flow", "node", "port", "data"):
                request.update({key: value})
        if self.message_client is None:
            request = pickle.dumps(request)
            self.Actions.append(request)
        else:
            if is_manager():
                
            self.message_client.send_request(COMMAND_HANDLER_MSG_TYPE, )

    def get_active_alerts(self) -> dict:
        """Gets a dictionary of the active alerts on this specific robot.

        Returns:
            dict: A dictionary inedexed by alert name which contains alert information.
        """
        robot_active_alerts = dict(self.Alerts)
        return robot_active_alerts

    def add_alert(self, alert: dict) -> None:
        """Adds a new entry to to the Alert dictionary of the robot on the redis-master.

        Args:
            alert (dict): The alert dictionary with the keys: info, action and callback.
        """
        alert.pop("status")
        alert_name = alert.get("name")
        FleetRobot.check_alert_dictionary(alert)
        self.Alerts[alert_name] = alert

    def remove_alert(self, alert: str) -> None:
        """Removes an entry from the Alert dictionary of the robot on redis-master.

        Args:
            alert (str): The name of the alert to be removed.
        """
        active_alerts = self.get_active_alerts()
        if alert in active_alerts:
            # active_alerts.pop(alert)
            self.Alerts.pop(alert)

    @staticmethod
    def check_alert_dictionary(alert: dict) -> None:
        """Checks if the alert dictionary contains all the required fileds.
        if not logs a warning.

        Args:
            alert (dict): The alert dict.
        """
        for field in ("info", "action", "callback"):
            if field not in alert:
                logger.warning(f"The field: {field} is missing from alert dictionary")

    @staticmethod
    def get_robot_key_by_ip(ip_address: str, key_name: str) -> bytes:
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
