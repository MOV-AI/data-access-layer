
from dal.scopes.scope import Scope
from dal.scopes.robot import Robot
from movai_core_shared.logger import Log

LOGGER = Log.get_logger("dal.mov.ai")


class Alert(Scope):
    def __init__(self, alert_id: str = "", new=False, db="global"):
        super().__init__(scope="Alert", alert_id=alert_id, new=new, db=db)

    def activate(self, **kwargs):
        Robot().add_active_alert(self.alert_id, info=self.info, action=self.action, alert_label=self.alert_label, info_params=kwargs)

    def deactivate(self):
        Robot().remove_alert(self.alert_id)

    def clear_alerts(self):
        Robot().clear_alerts(self.alert_id)