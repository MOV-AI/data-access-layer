"""
metrics request fields:
{
    'req_type': "metrics",
    "created": "##########",
    "robot_info": {
        "fleet": "movai",
        "robot_id": "########",
        "robot": "robotname"
        "service_name: "servicename"
    },
    'req_data': {
        "metric_type": "alerts",
        'measurement': "metric_logs",
        "metric_data": {}
        }
    }
}
"""
from typing import Optional

from pydantic import BaseModel
from dal.messages.general_data import Request


class MetricData(BaseModel):
    measurement: str
    metric_type: str
    metric_fields: Optional[dict]
    metric_tags: Optional[dict]

    def __str__(self) -> str:
        text = f"""
            measurement: {self.measurement}
            metric_type: {self.metric_type}
            metric_fields: {self.metric_fields}
            metric_tags: {self.metric_tags}
        """
        return text


class MetricRequest(Request):
    req_data: MetricData

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


class QueryData(BaseModel):
    limit: int
    offset: int
    tags: Optional[dict]
    robots: Optional[list]
    from_: Optional[int]
    to_: Optional[int]

    def __str__(self) -> str:
        text = f"""
                limit: {self.limit}
                offset: {self.offset}
                tags: {self.tags}
                robots: {self.robots}
                from_: {self.from_}
                to_: {self.to_}
        """
        return text


class MetricQueryData(BaseModel):
    measurement: str
    query_data: QueryData

    def __str__(self) -> str:
        text = f"""
            measurement: {self.measurement}
            query_data: {self.query_data.__str__()}
        """
        return text


class MetricQueryRequest(Request):
    req_data: MetricQueryData

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
