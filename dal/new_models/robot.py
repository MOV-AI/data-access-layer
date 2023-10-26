import pickle
import uuid
import pydantic
from .base_model.redis_model import RedisModel
from .configuration import Configuration
from .base_model.common import PrimaryKey

"""
    {'Robot': {'dde2a5de3b074f39956792785637ca3e': {'IP': '127.0.0.1',
   'RobotName': 'tugbot-24-70',
   'Status': {'active_flow': '',
    'active_scene': '',
    'active_states': [],
    'core_lchd': [],
    'locks': [],
    'nodes_lchd': [],
    'persistent_nodes_lchd': [],
    'timestamp': 1688980993.2879748},
   'Actions': [],
   'Notifications': [],
   'Alerts': {},
   'Label': '',
   'Info': ''}}}


    Returns:
        _type_: _description_
    """


class RobotStatus(pydantic.BaseModel):
    active_flow: str = None
    active_scene: str = None
    active_states: list = pydantic.Field(default_factory=list)
    core_lchd: list = pydantic.Field(default_factory=list)
    locks: list = pydantic.Field(default_factory=list)
    nodes_lchd: list = pydantic.Field(default_factory=list)
    persistent_nodes_lchd: list = pydantic.Field(default_factory=list)
    timestamp: float = None


class Robot(RedisModel, extra=pydantic.Extra.allow):
    IP: str = "127.0.0.1"
    RobotName: str
    Status: RobotStatus = RobotStatus()
    Actions: list = pydantic.Field(default_factory=list)
    Notifications: list = pydantic.Field(default_factory=list)
    Alerts: dict = pydantic.Field(default_factory=dict)
    Parameter: dict = pydantic.Field(default_factory=dict)

    def __init__(self, *args, **kwargs):
        if not args and not kwargs:
            robots = self.db("local").keys("*:Robot:*")
            if not robots:
                # no robot exist so we create one
                unique_id = uuid.uuid4()
                pk = PrimaryKey.create_pk(
                    project="Movai", scope="Robot", id=unique_id.hex, version=""
                )
                robot_name = f"robot_{unique_id.hex[0:6]}"
                super().__init__(pk=pk, RobotName=robot_name)
                self.save("local")
                self.save("global")
            else:
                pk = self.db("local").keys("*:Robot:*")[0].decode()
                obj = self.db("local").json().get(pk)
                super().__init__(**obj)

            # TODO need to be tested
            self.fleet = Robot(**self.model_dump())

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
        states = Configuration(self.RobotName).get_param("states")

        return {} if not states else states

    def set_param(self, param: str, value, db: str = "all"):
        """Sets or updates a parameter of the robots"""
        self.Parameter[param].Value = value

    @classmethod
    def cls_update_status(cls, robot_name: str, status: dict, db: str = "all"):
        """Class method to update the Robot status in the database
        This method reduces readings from the database compared to using Robot instance
        """

        to_send = {"Robot": {robot_name: {"Status": status}}}
        if db in ["all", "global"]:
            MovaiDB("global").set(to_send)
        if db in ["all", "local"]:
            MovaiDB("local").set(to_send)

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
