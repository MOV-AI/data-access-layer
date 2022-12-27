"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential
   Usage:
        Base class for all remote message handler.
        Sends messages to the robot Message-Server component
   Developers:
   - Dor Marcous (dor@mov.ai) - 2022
"""
import json
import random

from movai_core_shared.logger import Log
from movai_core_shared.core.zmq_client import ZmqClient
from movai_core_shared.envvars import (
    MOVAI_ZMQ_TIMEOUT_MS,
    MOVAI_MSG_SERVER_PORT,
    MOVAI_ZMQ_IP,
    FLEET_NAME
)
from dal.classes.utils.robot_info import RobotInfo


class MessageClient(ZmqClient):
    def __init__(self, msg_type, measurement, msg_server_ip=MOVAI_ZMQ_IP, msg_server_port=MOVAI_MSG_SERVER_PORT, timeout_ms=MOVAI_ZMQ_TIMEOUT_MS, server_pub_key=""):
        """
        constructor
        Args:
            msg_type: The handler name for handling the message
            measurement: The time-series DB name for storing the data
            msg_server_ip (str): The ip of the msg server, default by env var MOVAI_ZMQ_IP to localhost
            msg_server_port (str): The port of the message server, default by env var MOVAI_MSG_SERVER_PORT to 8082
            timeout_ms (str/int): The time in miliseconds that will drop the message, 0 to infinte, default by env var MOVAI_ZMQ_TIMEOUT_MS
            server_pub_key (str): The public key of the server, in case it's encrypted, default no encryption
        """
        self._get_robot_info()

        self._msg_type = msg_type
        self._measurement = measurement
        self._logger = Log.get_logger("MessageClient")
        random.seed() # setting the seed for the random number generator
        identity = f"{msg_type}_message_client_{random.getrandbits(24)}"
        super().__init__(ip=msg_server_ip, port=msg_server_port, pub_key=server_pub_key, name=identity, timeout_ms=timeout_ms)

        self._logger.debug(f" {msg_type} client connected to local message server on {msg_server_ip}:{msg_server_port}")


    def send_request(self, data: dict):
        """
        Wrap the data into a message request and sent it to the robot message server
        Args:
            data: The message data to be sent to the robot message server
        """
        # Add tags to the request data
        data['tags'] = {
            'fleet': self._fleet,
            'robot_id': self._robot_id,
            'robot': self._robot_name
        }

        request_data = {
            'request': {
                'req_type': self._msg_type,
                'measurement': self._measurement,
                'req_data': data
            }
        }
        self.send_msg(request_data, wait_for_response=False)

    def _get_robot_info(self):
        """
        get the Robot info from the local Redis DB
        and the fleet name from an environment parameter
        """
        self._robot_id = RobotInfo.get_id()
        self._robot_name = RobotInfo.get_name()
        self._fleet = FLEET_NAME


