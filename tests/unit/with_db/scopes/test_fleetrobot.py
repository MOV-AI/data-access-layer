"""Tests for FleetRobot scope."""


class TestFleetRobot:
    def test_get_manager_and_get_members(self, global_db, delete_all_robots):
        """Test get_manager and get_members."""
        from dal.scopes.fleetrobot import FleetRobot, Role
        from dal.scopes.robot import Robot

        assert not FleetRobot.get_members()
        assert FleetRobot.get_manager() is None

        robot = Robot()

        assert not FleetRobot.get_members()
        assert FleetRobot.get_manager() is None

        robot.set_role(Role.MANAGER)

        assert not FleetRobot.get_members()
        assert FleetRobot.get_manager() == robot.name

        robot.set_role(Role.MEMBER)

        assert FleetRobot.get_members() == [robot.name]
        assert FleetRobot.get_manager() is None
