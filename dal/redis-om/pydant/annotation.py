from typing import Dict, Optional, Any, Union
import pydantic
from base import MovaiBaseModel

PARAMETER_KEY_REGEX = pydantic.constr(regex=r"^[0-9a-zA-Z_]+$")
FIELD_KEY_REGEX = pydantic.constr(regex=r"^[0-9a-zA-Z_!@?-]+$")


class FieldValue(pydantic.BaseModel):
    Type: Optional[str] = None
    Value: Optional[Union[str, bool]] = None


class Annotation(MovaiBaseModel):
    Type: Optional[str] = None
    Policy: Optional[str] = None
    Parameter: Optional[Dict[PARAMETER_KEY_REGEX, Any]] = None
    Field: Optional[Dict[FIELD_KEY_REGEX, FieldValue]] = None

    class Meta:
        model_key_prefix = "Annotation"


if __name__ == "__main__":
    A = Annotation(
        **{
            "Annotation": {
                "risk_prevention_warning": {
                    "Field": {
                        "risk_prevention": {"Type": "config", "Value": "tugbot_risk_prevention.warning"}
                    },
                    "Label": "risk_prevention_warning",
                    "LastUpdate": {"date": "05/05/2022 at 14:31:27", "user": "movai"},
                    "Parameter": {"risk_prevention": "tugbot_risk_prevention.warning"},
                    "Policy": "",
                    "Type": "",
                    "User": "",
                }
            }
        }
    )

    A.save()
    print(Annotation.select())
