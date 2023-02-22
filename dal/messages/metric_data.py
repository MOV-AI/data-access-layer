import pydantic


class AlertData(pydantic.BaseModel):
    name: str
    info: str
    action: str
    callback: str
    status: str
    send_email: bool = False


class MetricData(pydantic.BaseModel):
    metric_type: str = "alerts"
    measurement: str
    metric_data: AlertData  # should change to Union in case there is new types
