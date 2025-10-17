from dal.scopes.scope import Scope
from dal.scopes.robot import Robot
from movai_core_shared.logger import Log

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
        super().__init__(scope="Alert", name=alert_id, version=version, new=new, db=db)

    def activate(self,**kwargs):
        Robot().add_active_alert(
            self.AlertId,
            info=self.Info,
            action=self.Action,
            alert_label=self.AlertLabel,
            info_params=kwargs,
        )

    def deactivate(self):
        alert_metric = Robot().pop_alert(self.AlertId)
        if enterprise:
            self.alert_metrics.add("alert_events", **alert_metric)

    def clear_alerts(self):
        alert_metrics = Robot().clear_alerts()
        if enterprise:
            for alert_metric in alert_metrics:
                self.alert_metrics.add("alert_events", **alert_metric)
