from base import MovaiBaseModel
from typing import Any


class Application(MovaiBaseModel):
    User: str
    Type: str
    Package: str
    EntryPoint: str
    Icon: str
    Configuration: str
    CustomConfiguration: str
    Callbacks: Any


a = Application(
    **{
        "Application": {
            "application1": {
                "Label": "str",
                "LastUpdate": "str",
                "Version": "str",
                "Description": "str",
                "User": "str",
                "Type": "str",
                "Package": "str",
                "EntryPoint": "str",
                "Icon": "str",
                "Configuration": "str",
                "CustomConfiguration": "str",
                "Callbacks": "any",
            }
        }
    })

a.save()