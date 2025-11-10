from datetime import datetime
import pytest

from movai_core_shared.messages.alert_data import AlertActivationData
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
        assert alert_id in robot.get_active_alerts()
        assert len(robot.fleet.ActiveAlerts) == 1

        # Remove the alert
        robot.pop_alert(alert_id)
        assert alert_id not in robot.get_active_alerts()
        assert alert_id not in robot.fleet.ActiveAlerts

        # Add multiple alerts and clear all
        robot.add_active_alert(
            "a1", AlertActivationData(args="{}", activation_date=datetime.now().isoformat())
        )
        robot.add_active_alert(
            "a2", AlertActivationData(args="{}", activation_date=datetime.now().isoformat())
        )
        assert set(robot.get_active_alerts()) == {"a1", "a2"}
        assert len(robot.fleet.ActiveAlerts) == 2

        robot.clear_alerts()
        assert not robot.get_active_alerts()
        assert robot.fleet.ActiveAlerts == {}


@pytest.fixture(scope="class", autouse=True)
def import_alerts(request, metadata_folder):
    """Fixture to import alerts before running tests in the class."""
    from dal.tools.backup import Importer

    tool = Importer(
        metadata_folder,
        force=True,
        dry=False,
        debug=False,
        recursive=False,
        clean_old_data=True,
    )
    data = {"Alert": ["delete_me", "delete_me_placeholders"]}
    tool.run(data)


class TestAlerts:
    def test_alert_activation_deactivation(self, global_db):
        """Test that Alert activation and deactivation works properly."""

        robot = Robot()

        if hasattr(robot.fleet, "ActiveAlerts"):
            robot.fleet.ActiveAlerts.clear()

        alert_id = "delete_me"
        alert = Alert(alert_id)

        # Activate the alert
        alert.activate(param1="value1")

        # Check that the alert is in ActiveAlerts
        assert alert_id in robot.fleet.ActiveAlerts

        # Verify the contents of the active alert
        entry = robot.fleet.ActiveAlerts[alert_id]
        assert datetime.fromisoformat(entry["activation_date"])
        assert entry["args"] == '{"param1": "value1"}'

        # Deactivate the alert
        alert.deactivate()
        # Check that the alert is removed from ActiveAlerts
        assert alert_id not in robot.fleet.ActiveAlerts

    def test_alert_deactivation_nonexistent(self, global_db, caplog):
        """Test that deactivating a non-existent alert is handled gracefully."""

        robot = Robot()

        if hasattr(robot.fleet, "ActiveAlerts"):
            robot.fleet.ActiveAlerts.clear()

        alert_id = "delete_me"
        alert = Alert(alert_id)

        # Deactivate the alert which was never activated
        alert.deactivate()

        # Check the logs for the expected warning message
        assert f"Alert {alert_id} not active, cannot deactivate" in caplog.text

        # Ensure ActiveAlerts is still empty
        assert robot.fleet.ActiveAlerts == {}

    def test_alert_activation_with_placeholders(self, global_db):
        """Test that activating an alert with placeholders works properly."""

        robot = Robot()

        if hasattr(robot.fleet, "ActiveAlerts"):
            robot.fleet.ActiveAlerts.clear()

        alert_id = "delete_me_placeholders"
        alert = Alert(alert_id)

        # Activate the alert with required parameters
        alert.activate(placeholder="filled_value")

        # Check that the alert is in ActiveAlerts
        assert alert_id in robot.fleet.ActiveAlerts

        # Verify the contents of the active alert
        entry = robot.fleet.ActiveAlerts[alert_id]
        assert datetime.fromisoformat(entry["activation_date"])
        assert entry["args"] == '{"placeholder": "filled_value"}'

        # Deactivate the alert
        alert.deactivate()
        # Check that the alert is removed from ActiveAlerts
        assert alert_id not in robot.fleet.ActiveAlerts

    def test_alert_activation_with_missing_parameters(self, global_db, caplog):
        """Test that activating an alert with missing parameters is handled properly."""

        robot = Robot()

        if hasattr(robot.fleet, "ActiveAlerts"):
            robot.fleet.ActiveAlerts.clear()

        alert_id = "delete_me_placeholders"
        alert = Alert(alert_id)

        # Activate the alert without required parameters
        alert.activate()  # No parameters provided

        # Check the logs for the expected error message
        assert (
            f"[alerts:True|user_log:True] Failed to activate alert {alert_id} due to missing key: 'placeholder' for Info text: Random info with placeholder {{placeholder}}"
            in caplog.text
        )

        # Check that the alert is in ActiveAlerts
        assert alert_id in robot.fleet.ActiveAlerts

    def test_alert_clear_all(self, global_db):
        """Test that clearing all alerts works properly."""

        robot = Robot()

        if hasattr(robot.fleet, "ActiveAlerts"):
            robot.fleet.ActiveAlerts.clear()

        # Add multiple alerts
        alert1 = Alert("delete_me")
        alert2 = Alert("delete_me_placeholders")

        alert1.activate()
        alert2.activate(placeholder="value")

        assert "delete_me" in robot.fleet.ActiveAlerts
        assert "delete_me_placeholders" in robot.fleet.ActiveAlerts

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
        alert_id = "delete_me"
        alert = Alert(alert_id)
        duplicate_alert = Alert(alert_id)

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

    def test_alert_is_active_classmethod(self, global_db):
        """Test that the Alert.is_active classmethod works properly."""

        robot = Robot()

        if hasattr(robot.fleet, "ActiveAlerts"):
            robot.fleet.ActiveAlerts.clear()

        alert_id = "delete_me"
        alert = Alert(alert_id)

        # Ensure other alerts do not interfere
        dummy_alert_id = "delete_me_placeholders"
        dummy_alert = Alert(dummy_alert_id)
        dummy_alert.activate(placeholder="value")

        # Initially, the alert should not be active
        assert not Alert.is_active(alert_id)
        assert Alert.is_active(dummy_alert_id)

        alert.activate()

        assert Alert.is_active(alert_id)
        assert Alert.is_active(dummy_alert_id)

        alert.deactivate()

        assert not Alert.is_active(alert_id)
        assert Alert.is_active(dummy_alert_id)

    def test_get_active_alerts_classmethod(self, global_db):
        """Test that the Alert.get_active classmethod works properly."""

        robot = Robot()

        if hasattr(robot.fleet, "ActiveAlerts"):
            robot.fleet.ActiveAlerts.clear()

        alert1_id = "delete_me"
        alert2_id = "delete_me_placeholders"
        alert1 = Alert(alert1_id)
        alert2 = Alert(alert2_id)

        # Initially, there should be no active alerts
        assert not Alert.get_active()

        alert1.activate()

        assert Alert.get_active() == [alert1_id]

        alert2.activate(placeholder="value")

        assert set(Alert.get_active()) == {alert1_id, alert2_id}

        alert1.deactivate()

        assert Alert.get_active() == [alert2_id]

        alert2.deactivate()

        assert not Alert.get_active()
