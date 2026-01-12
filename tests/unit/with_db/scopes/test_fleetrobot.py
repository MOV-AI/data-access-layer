"""Tests for FleetRobot scope."""


class TestFleetRobot:
    def test_get_manager_and_get_members(self, global_db, delete_all_robots):
        """Test get_manager and get_members."""
        from dal.scopes.fleetrobot import FleetRobot, Role
        from dal.scopes.robot import Robot

        assert not FleetRobot.get_members()
        assert FleetRobot.get_manager() is None

        robot = Robot()

        assert FleetRobot(robot.name).is_manager() is False
        assert not FleetRobot.get_members()
        assert FleetRobot.get_manager() is None

        robot.set_role(Role.MANAGER)

        assert FleetRobot(robot.name).is_manager() is True
        assert not FleetRobot.get_members()
        assert FleetRobot.get_manager() == robot.name

        robot.set_role(Role.MEMBER)

        assert FleetRobot(robot.name).is_manager() is False
        assert FleetRobot.get_members() == [robot.name]
        assert FleetRobot.get_manager() is None

    def test_name_and_id(self, global_db, delete_all_robots):
        """Test name and id methods."""
        from dal.scopes.fleetrobot import FleetRobot
        from dal.scopes.robot import Robot

        robot = Robot()
        robot_id = robot.name
        robot_name = robot.RobotName

        assert FleetRobot.name_to_id(robot_name) == robot_id
        assert FleetRobot.id_to_name(robot_id) == robot_name
