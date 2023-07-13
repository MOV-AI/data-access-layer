from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, constr
from .base_model import MovaiBaseModel, Arg


WIDGET_REGEX = r"^(Button|Selector|Input|Label|Divider|Joystick|VideoPanel|Toggle|Scene|StartFlow)[0-9]*$"


class WidgetInst(BaseModel):
    Template: Optional[str] = None
    # Parameter: Optional[ArgSchema] = None
    Parameter: Optional[Dict[constr(regex=r"^[a-zA-Z0-9_]+$"), Arg]] = None


class Layout(MovaiBaseModel):
    Icon: Optional[
        str
    ] = None  # currently this field is deprecated, maybe will be in used in the future
    DashboardTitle: Optional[
        str
    ] = None  # currently this field is deprecated, maybe will be in used in the future
    Styles: Optional[str] = None
    WidgetInst: Optional[
        Dict[
            constr(regex=WIDGET_REGEX),
            WidgetInst,
        ]
    ] = None
    LayoutColors: Optional[List] = None

    # https: // movai.atlassian.net / browse / BP - 749
    # missing fields:
    # allLayouts
    # layoutEvents

    class Meta:
        model_key_prefix = "Layout"
