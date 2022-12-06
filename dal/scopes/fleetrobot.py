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

from movai_core_shared.logger import Log

from .classes.protocols.zmq_client import ZmqClient

from .scope import MovaiDB, Scope

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
        db = MovaiDB('global')
        robot_id = None
        for key, val in db.search_by_args(scope='Robot')[0]['Robot'].items():
            if val['RobotName'] == name:
                robot_id = key
                break
        if robot_id is None:
            logger.error(f"robot {name} not found in DB")
        ip_key = {'Robot': {robot_id: {'IP': {}}}}
        self.ip = db.get_value(ip_key)
        # Todo: add public key from redis to the zmq client
        self.zmq_client = ZmqClient(self.ip, name=name)

    def send_cmd(self, command, *, flow=None, node=None, port=None, data=None) -> None:
        """Send an action command to the Robot"""
        to_send = {}
        for key, value in locals().items():
            if value is not None and key in ("command", "flow", "node", "port", "data"):
                to_send.update({key: value})
        self.zmq_client.send_msg(to_send)

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
        alert_name = alert.get("alert_name")
        FleetRobot.check_alert_dictionary(alert)
        self.Alerts[alert_name] = alert

    def remove_alert(self, alert: str) -> None:
        """Removes an entry from the Alert dictionary of the robot on redis-master.

        Args:
            alert (str): The name of the alert to be removed.
        """
        active_alerts = self.get_active_alerts()
        if alert in active_alerts:
            #active_alerts.pop(alert)
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
