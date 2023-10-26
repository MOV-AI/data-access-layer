from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import StringConstraints, BaseModel, Field
from .base_model import MovaiBaseModel, Arg
from typing_extensions import Annotated


WIDGET_REGEX = (
    r"^(Button|Selector|Input|Label|Divider|Joystick|VideoPanel|Toggle|Scene|StartFlow)[0-9]*$"
)


class WidgetInstValue(BaseModel):
    Template: Optional[str] = None
    # Parameter: Optional[ArgSchema] = None
    Parameter: Optional[
        Dict[Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_]+$")], Arg]
    ] = Field(default_factory=dict)


class Layout(MovaiBaseModel):
    # currently this field is deprecated, maybe will be in used in the future
    Icon: Optional[
        str
    ] = None

    # currently this field is deprecated, maybe will be in used in the future
    DashboardTitle: Optional[
        str
    ] = None
    Styles: Optional[str] = None
    WidgetInst: Optional[
        Dict[
            Annotated[str, StringConstraints(pattern=WIDGET_REGEX)],
            WidgetInstValue,
        ]
    ] = Field(default_factory=dict)
    LayoutColors: Optional[List] = None

    # https: // movai.atlassian.net / browse / BP - 749
    # missing fields:
    # allLayouts
    # layoutEvents
