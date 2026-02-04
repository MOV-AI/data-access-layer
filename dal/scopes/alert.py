import json
from datetime import datetime
from threading import Lock
from typing import List
from functools import cached_property

from dal.scopes.scope import Scope
from dal.scopes.robot import Robot
from movai_core_shared.logger import Log
from movai_core_shared.consts import DeactivationType
from movai_core_shared.messages.alert_data import AlertActivationData

try:
    from movai_core_enterprise.message_client_handlers._alert_metrics import AlertMetricsFactory

    enterprise = True
except ImportError:
    enterprise = False

LOGGER = Log.get_user_logger("dal.mov.ai", alerts=True)


class Alert(Scope):
    scope = "Alert"
    alert_metrics = None
    _lock = Lock()

    def __init__(self, name, version="latest", new=False, db="global"):
        self.__dict__["alert_id"] = name
        super().__init__(scope="Alert", name=name, version=version, new=new, db=db)

    @cached_property
    def _robot(self):
        """Instantiates the robot object, caching it."""
        return Robot()

    def validate_parameters(self, name: str, text: str, **kwargs):
        """Validate that all required placeholders in the text are provided in kwargs.

        Args:
            name (str): The name of the field being validated (e.g., "Title").
            text (str): The text containing placeholders to validate.
            **kwargs: Parameters to fill the placeholders in the text.

        """
        try:
            text.format(**kwargs)
        except KeyError as e:
            LOGGER.error(
                "Failed to activate alert %s due to missing key: %s for %s text: %s",
                self.alert_id,
                e,
                name,
                text,
            )
        except ValueError as e:
            LOGGER.error(
                "Failed to activate alert %s due to formatting error: %s for %s text: %s",
                self.alert_id,
                e,
                name,
                text,
            )
        except Exception as e:
            LOGGER.error("Formatting error for alert %s: %s", self.alert_id, e, exc_info=True)

    def activate(self, **kwargs):
        """Activate the alert, adding it to the active alerts list if validation passes.

        Args:
            **kwargs: Parameters to fill placeholders in Title, Info, and Action fields.

        """
        # Verify that all necessary activation fields were provided
        self.validate_parameters("Title", self.Title, **kwargs)
        self.validate_parameters("Info", self.Info, **kwargs)
        self.validate_parameters("Action", self.Action, **kwargs)

        # if not serializable, convert to string
        args = json.dumps(kwargs, default=str)
        self._robot.add_active_alert(
            self.alert_id,
            AlertActivationData(args=args, activation_date=datetime.now().isoformat()),
        )

    def deactivate(self, deactivation_type: str = DeactivationType.REQUESTED):
        """Deactivate the alert, removing it from the active alerts list.

        Args:
            deactivation_type (str, optional): The type of deactivation. Defaults to DeactivationType.REQUESTED.

        """
        alert_metric = self._robot.pop_alert(self.alert_id, deactivation_type=deactivation_type)

        if not alert_metric:
            LOGGER.warning("Alert %s not active, cannot deactivate", self.alert_id)
            return

        if enterprise:
            Alert.get_alert_metrics_handler().add("alert_events", **alert_metric.model_dump())

    @classmethod
    def clear_alerts(cls, deactivation_type: str = DeactivationType.REQUESTED):
        """Clear all active alerts.

        Args:
            deactivation_type (str, optional): The type of deactivation. Defaults to DeactivationType.REQUESTED.

        """
        alert_metrics = Robot().clear_alerts(deactivation_type=deactivation_type)
        if enterprise:
            for alert_metric in alert_metrics:
                Alert.get_alert_metrics_handler().add("alert_events", **alert_metric.model_dump())

    @classmethod
    def get_active(cls) -> List[str]:
        """Get a list of active alert IDs.

        Returns:
            List[str]: List of active alert IDs.
        """
        return Robot()._get_active_alerts()

    @classmethod
    def is_active(cls, alert_id: str) -> bool:
        """Check if a specific alert is active.

        Args:
            alert_id (str): The ID of the alert to check.

        Returns:
            bool: True if the alert is active, False otherwise.
        """
        return alert_id in Robot()._get_active_alerts()

    @classmethod
    def get_alert_metrics_handler(cls):
        with Alert._lock:
            if enterprise and Alert.alert_metrics is None:
                Alert.alert_metrics = AlertMetricsFactory.create()

        return Alert.alert_metrics
