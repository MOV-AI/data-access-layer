import json
from datetime import datetime
from threading import Lock

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

    def validate_parameters(self, name: str, text: str, **kwargs):
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
        # Verify that all necessary activation fields were provided
        self.validate_parameters("Title", self.Title, **kwargs)
        self.validate_parameters("Info", self.Info, **kwargs)
        self.validate_parameters("Action", self.Action, **kwargs)

        # if not serializable, convert to string
        args = json.dumps(kwargs, default=str)
        Robot().add_active_alert(
            self.alert_id,
            AlertActivationData(args=args, activation_date=datetime.now().isoformat()),
        )

    def deactivate(self, deactivation_type: str = DeactivationType.REQUESTED):
        alert_metric = Robot().pop_alert(self.alert_id, deactivation_type=deactivation_type)

        if not alert_metric:
            LOGGER.warning("Alert %s not active, cannot deactivate", self.alert_id)
            return

        if enterprise:
            Alert.get_alert_metrics_handler().add("alert_events", **alert_metric.model_dump())

    @classmethod
    def clear_alerts(cls, deactivation_type: str = DeactivationType.REQUESTED):
        alert_metrics = Robot().clear_alerts(deactivation_type=deactivation_type)
        if enterprise:
            for alert_metric in alert_metrics:
                Alert.get_alert_metrics_handler().add("alert_events", **alert_metric.model_dump())

    @classmethod
    def get_alert_metrics_handler(cls):
        with Alert._lock:
            if enterprise and Alert.alert_metrics is None:
                Alert.alert_metrics = AlertMetricsFactory.create()

        return Alert.alert_metrics
