
from dal.scopes.scope import Scope
from dal.scopes.robot import Robot
from movai_core_shared.logger import Log

LOGGER = Log.get_logger("dal.mov.ai")


class Alert(Scope):
    scope = "Alert"
    def __init__(self, alert_id: str = "",version="latest", new=False, db="global"):
        super().__init__(scope="Alert", name=alert_id, version=version, new=new, db=db)

    def activate(self, **kwargs):
        Robot().add_active_alert(self.AlertId, info=self.Info, action=self.Action, alert_label=self.AlertLabel, info_params=kwargs)

    def deactivate(self):
        Robot().remove_alert(self.AlertId)

    def clear_alerts(self):
        Robot().clear_alerts(self.AlertId)