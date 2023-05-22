from pydantic import BaseModel

from dal.messages.general_data import Request


class MetricData(BaseModel):
    name: str
    info: str
    action: str
    callback: str
    status: str
    send_email: bool = False

    def __str__(self) -> str:
        text = f"""
                name: {self.name}
                info: {self.info}
                action: {self.action}
                callback: {self.callback}
                status: {self.status}
                send_email: {self.send_email}
        """
        return text


class AlertData(BaseModel):
    measurement: str
    metric_type: str
    metric_data: MetricData

    def __str__(self) -> str:
        text = f"""
            measurement: {self.measurement}
            metric_type: {self.metric_type}
            metric_data: {self.metric_data.__str__()}
        """
        return text


class AlertRequest(Request):
    req_data: AlertData

    def __str__(self):
        text = f"""
        ===========================================================================================
        req_type: {self.req_type}
        response_required: {self.response_required}
        req_data: {self.req_data.__str__()}
        robot_info: {self.robot_info.__str__()}
        created: {self.created}
        ==========================================================================================="""
        return text
