"""Tests for dal.scopes.fleetrobot module."""


class TestFleetRobot:
    def test_remove_entry(self, global_db):
        """Test removing a fleet robot."""
        from dal.scopes.robot import Robot
        from dal.scopes.fleetrobot import FleetRobot

        robot_name = "test_robot"
        robot = Robot()
        robot.set_name(robot_name)

        FleetRobot.remove_entry(robot.name)
