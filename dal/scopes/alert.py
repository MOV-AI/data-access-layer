from dal.scopes.scope import Scope
from dal.scopes.robot import Robot
from movai_core_shared.logger import Log
from movai_core_shared.consts import DeactivationType
from threading import Lock

try:
    from movai_core_enterprise.message_client_handlers._alert_metrics import AlertMetricsFactory

    enterprise = True
except ImportError:
    enterprise = False

LOGGER = Log.get_logger("dal.mov.ai")


class Alert(Scope):
    scope = "Alert"
    alert_metrics = None
    _lock = Lock()

    def __init__(self, alert_id: str = "", version="latest", new=False, db="global"):
        self.__dict__["alert_id"] = alert_id
        super().__init__(scope="Alert", name=alert_id, version=version, new=new, db=db)

    def activate(self, **kwargs):
        Robot().add_active_alert(
            self.alert_id,
            info=self.Info,
            label=self.Label,
            action=self.Action,
            title=self.Title,
            info_params=kwargs,
        )

    def deactivate(self, deactivation_type: str = DeactivationType.REQUESTED):
        alert_metric = Robot().pop_alert(self.alert_id, deactivation_type=deactivation_type)
        if enterprise:
            Alert.get_alert_metrics_handler().add("alert_events", **alert_metric)

    @classmethod
    def clear_alerts(cls, deactivation_type: str = DeactivationType.REQUESTED):
        alert_metrics = Robot().clear_alerts(deactivation_type=deactivation_type)
        if enterprise:
            for alert_metric in alert_metrics:
                Alert.get_alert_metrics_handler().add("alert_events", **alert_metric)

    @classmethod
    def get_alert_metrics_handler(cls):
        with Alert._lock:
            if enterprise and Alert.alert_metrics is None:
                Alert.alert_metrics = AlertMetricsFactory.create()

        return Alert.alert_metrics
