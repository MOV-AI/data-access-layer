from dal.scopes.alert import Alert
from dal.scopes.robot import Robot


class TestRobotActiveAlerts:
    def test_add_remove_clear_active_alerts(self, global_db):
        """Test that ActiveAlerts is properly added, removed, and cleared."""

        robot = Robot()

        if hasattr(robot.fleet, "ActiveAlerts"):
            robot.fleet.ActiveAlerts.clear()

        # Add a new active alert
        alert_id = "alert_001"
        robot.add_active_alert(
            alert_id=alert_id,
            label="test_label",
            info="Test info",
            title="Test Title",
            action="Test action",
        )

        assert "ActiveAlerts" in robot.fleet.__dict__
        assert alert_id in robot.fleet.ActiveAlerts

        entry = robot.fleet.ActiveAlerts[alert_id]
        assert entry["Label"] == "test_label"
        assert entry["Info"] == "Test info"
        assert entry["Title"] == "Test Title"
        assert entry["Action"] == "Test action"
        assert "activation_date" in entry

        # Try adding the same alert again
        robot.add_active_alert(alert_id, info="Duplicate")
        # should not duplicate
        assert len(robot.fleet.ActiveAlerts) == 1

        # Remove the alert
        robot.pop_alert(alert_id)
        assert alert_id not in robot.fleet.ActiveAlerts

        # Add multiple alerts and clear all
        robot.add_active_alert("a1", info="i1")
        robot.add_active_alert("a2", info="i2")
        assert len(robot.fleet.ActiveAlerts) == 2

        robot.clear_alerts()
        assert robot.fleet.ActiveAlerts == {}


class TestAlerts:
    def test_alert_activation_deactivation(self, global_db):
        """Test that Alert activation and deactivation works properly."""

        robot = Robot()

        if hasattr(robot.fleet, "ActiveAlerts"):
            robot.fleet.ActiveAlerts.clear()

        alert_id = "alert_001"
        alert = Alert(alert_id=alert_id, new=True)

        # Activate the alert
        alert.activate(param1="value1")

        # Check that the alert is in ActiveAlerts
        assert alert_id in robot.fleet.ActiveAlerts

        # Verify the contents of the active alert
        entry = robot.fleet.ActiveAlerts[alert_id]
        assert entry["Info"] == alert.Info
        assert entry["Label"] == alert.Label
        assert entry["Title"] == alert.Title
        assert entry["Action"] == alert.Action
        assert entry["info_params"]["param1"] == "value1"

        # Deactivate the alert
        alert.deactivate()
        # Check that the alert is removed from ActiveAlerts
        assert alert_id not in robot.fleet.ActiveAlerts

    def test_alert_clear_all(self, global_db):
        """Test that clearing all alerts works properly."""

        robot = Robot()

        if hasattr(robot.fleet, "ActiveAlerts"):
            robot.fleet.ActiveAlerts.clear()

        # Add multiple alerts
        alert1 = Alert(alert_id="alert_001", new=True)
        alert2 = Alert(alert_id="alert_002", new=True)

        alert1.activate()
        alert2.activate()

        assert "alert_001" in robot.fleet.ActiveAlerts
        assert "alert_002" in robot.fleet.ActiveAlerts

        # Clear all alerts
        Alert.clear_alerts()

        # Check that ActiveAlerts is empty
        assert robot.fleet.ActiveAlerts == {}

    def test_duplicate_alert_activation_and_deactivation(self, global_db):
        """Test that activating the same alert multiple times does not duplicate it."""

        robot = Robot()

        if hasattr(robot.fleet, "ActiveAlerts"):
            robot.fleet.ActiveAlerts.clear()

        # Create two Alert instances with the same alert_id
        alert_id = "alert_001"
        alert = Alert(alert_id=alert_id, new=True)
        duplicate_alert = Alert(alert_id=alert_id, new=True)

        # Activate both alerts
        alert.activate()
        duplicate_alert.activate()

        # Check that there is only one instance of the alert
        assert len(robot.fleet.ActiveAlerts) == 1
        assert alert_id in robot.fleet.ActiveAlerts

        # Both alerts reference the same issue
        # Deactivating the alert using the duplicate instance should remove it
        duplicate_alert.deactivate()
        assert alert_id not in robot.fleet.ActiveAlerts
