import json
from datetime import datetime

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

LOGGER = Log.get_logger("dal.mov.ai")


class Alert(Scope):
    scope = "Alert"
    if enterprise:
        alert_metrics = AlertMetricsFactory.create()  # initialize metrics if enabled

    def __init__(self, alert_id: str = "", version="latest", new=False, db="global"):
        self.__dict__["alert_id"] = alert_id
        super().__init__(scope="Alert", name=alert_id, version=version, new=new, db=db)

    def activate(self, **kwargs):
        # if not serializable, convert to string
        args = json.dumps(kwargs, default=str)
        Robot().add_active_alert(
            self.alert_id,
            AlertActivationData(args=args, activation_date=datetime.now().isoformat()),
        )

    def deactivate(self, deactivation_type: str = DeactivationType.REQUESTED):
        alert_metric = Robot().pop_alert(self.alert_id, deactivation_type=deactivation_type)

        if not alert_metric:
            LOGGER.debug("Alert %s not active, cannot deactivate", self.alert_id)
            return

        if enterprise:
            self.alert_metrics.add("alert_events", **alert_metric.model_dump())

    @classmethod
    def clear_alerts(cls, deactivation_type: str = DeactivationType.REQUESTED):
        alert_metrics = Robot().clear_alerts(deactivation_type=deactivation_type)
        if enterprise:
            for alert_metric in alert_metrics:
                cls.alert_metrics.add("alert_events", **alert_metric.model_dump())
