"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020

   Module that implements Robot namespace
"""
import pickle
from threading import Timer
from enum import Enum
from .scope import Scope
from dal.movaidb import MovaiDB
from dal.models.var import Var
from movai_core_shared.logger import Log

RECOVERY_TIMEOUT_IN_SECS = 15
RECOVERY_STATE_KEY = "recovery_state"
RECOVERY_RESPONSE_KEY = "recovery_response"


class RecoveryStates(Enum):
    """Class for keeping recovery states. Values are stored in recovery_state fleet variable."""
    READY: str = "READY"
    IN_RECOVERY: str = "IN_RECOVERY"
    PUSHED: str = "PUSHED"
    NOT_AVAILABLE: str = "NOT_AVAILABLE"

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

    def send_cmd(self, command, *, flow=None, node=None, port=None, data=None) -> None:
        """Send an action command to the Robot"""
        to_send = {}
        for key, value in locals().items():
            if value is not None and key in ("command", "flow", "node", "port", "data"):
                to_send.update({key: value})

        to_send = pickle.dumps(to_send)

        self.Actions.append(to_send)

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

    def trigger_recovery_aux(self):
        """Set Var to trigger Recovery Robot.

        Args:
            robot_id (str): The id of the robot to trigger recovery.

        Raises:
            Exception: In case Var could not be found.
        """
        try:
            var_scope = Var(scope="fleet", _robot_name=self.name)
            var_scope.set(RECOVERY_STATE_KEY, RecoveryStates.PUSHED.value)
            # If the state doesn't change after 15 secs, set a VAR to send a message to the interface
            timeout = Timer(RECOVERY_TIMEOUT_IN_SECS, lambda: self.recovery_timeout())
            timeout.start()
        except Exception as exc:
            raise Exception("Caught exception in trigger recovery aux", exc)

    def recovery_timeout(self):
        """Handle recovery fail on timeout"""
        try:
            var_scope = Var(scope="fleet", _robot_name=self.name)
            recovery_state = var_scope.get(RECOVERY_STATE_KEY)

            if recovery_state == RecoveryStates.PUSHED.value:
                response = {
                    "success": False,
                    "message": "Failed to recover robot"
                }
                var_scope.set(RECOVERY_RESPONSE_KEY, response)
                var_scope.set(RECOVERY_STATE_KEY, RecoveryStates.NOT_AVAILABLE.value)
        except Exception as exc:
            raise Exception("Caught exception in recovery timeout", exc)

