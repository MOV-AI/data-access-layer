class TestRobotActiveAlerts:
    def test_add_remove_clear_active_alerts(self, global_db):
        """Test that ActiveAlerts is properly added, removed, and cleared."""
        from dal.scopes.robot import Robot

        robot = Robot()

        if hasattr(robot.fleet, "ActiveAlerts"):
            robot.fleet.ActiveAlerts.clear()

        # Add a new active alert
        alert_id = "alert_001"
        robot.add_active_alert(
            alert_id=alert_id,
            info="Test info",
            alert_label="Test label",
            action="Test action",
        )

        assert "ActiveAlerts" in robot.fleet.__dict__
        assert alert_id in robot.fleet.ActiveAlerts

        entry = robot.fleet.ActiveAlerts[alert_id]
        assert entry["alert_label"] == "Test label"
        assert entry["info"] == "Test info"
        assert entry["action"] == "Test action"
        assert "timestamp" in entry

        # Try adding the same alert again
        robot.add_active_alert(alert_id, info="Duplicate")
        # should not duplicate
        assert len(robot.fleet.ActiveAlerts) == 1

        # Remove the alert
        robot.remove_alert(alert_id)
        assert alert_id not in robot.fleet.ActiveAlerts

        # Add multiple alerts and clear all
        robot.add_active_alert("a1", info="i1")
        robot.add_active_alert("a2", info="i2")
        assert len(robot.fleet.ActiveAlerts) == 2

        robot.clear_alerts()
        assert robot.fleet.ActiveAlerts == {}
