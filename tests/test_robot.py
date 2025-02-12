import time
import unittest

import redis.exceptions

from dal.movaidb.database import MovaiDB
from dal.scopes.fleetrobot import FleetRobot


try:
    MovaiDB().db_read.ping()
    REDIS_AVAILABLE = True
except redis.exceptions.ConnectionError:
    REDIS_AVAILABLE = False


class TestRobot(unittest.TestCase):
    @unittest.skipUnless(REDIS_AVAILABLE, "Redis is not available")
    def test_robot_params(self):
        robot_name = FleetRobot.list_all()[0]
        robot = FleetRobot(robot_name)
        battery = robot.add("Parameter", "battery")
        battery.TTL = 3
        battery.Value = 100
        self.assertEqual(robot.Parameter["battery"].Value, 100)
        # wait for TTL to pass
        time.sleep(4)
        self.assertIsNone(robot.Parameter["battery"].Value)
