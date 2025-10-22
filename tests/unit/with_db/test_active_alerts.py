from datetime import datetime

from movai_core_shared.messages.alert_data import AlertActivationData


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
            alert_id,
            AlertActivationData(args="{}", activation_date=datetime.now().isoformat()),
        )

        assert "ActiveAlerts" in robot.fleet.__dict__
        assert alert_id in robot.fleet.ActiveAlerts

        entry = AlertActivationData(**robot.fleet.ActiveAlerts[alert_id])
        assert entry.args == "{}"
        assert datetime.fromisoformat(entry.activation_date)

        # Try adding the same alert again
        robot.add_active_alert(
            alert_id, AlertActivationData(args="{}", activation_date=datetime.now().isoformat())
        )
        # should not duplicate
        assert len(robot.fleet.ActiveAlerts) == 1

        # Remove the alert
        robot.pop_alert(alert_id)
        assert alert_id not in robot.fleet.ActiveAlerts

        # Add multiple alerts and clear all
        robot.add_active_alert(
            "a1", AlertActivationData(args="{}", activation_date=datetime.now().isoformat())
        )
        robot.add_active_alert(
            "a2", AlertActivationData(args="{}", activation_date=datetime.now().isoformat())
        )
        assert len(robot.fleet.ActiveAlerts) == 2

        robot.clear_alerts()
        assert robot.fleet.ActiveAlerts == {}
