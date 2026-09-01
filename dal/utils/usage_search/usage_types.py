"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Usage search scope mapping utilities.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Union


class DirectNodeUsageItem(BaseModel):
    """Single direct usage item for a Node."""

    node_instance_name: str


class IndirectNodeUsageItem(BaseModel):
    """Single indirect usage item for a Node - references immediate child flow."""

    flow_template_name: str
    flow_instance_name: str


class DirectFlowUsageItem(BaseModel):
    """Single direct usage item for a Flow."""

    flow_instance_name: str


class IndirectFlowUsageItem(BaseModel):
    """Single indirect usage item for a Flow - references immediate child flow."""

    flow_template_name: str
    flow_instance_name: str


class DirectCallbackUsageItem(BaseModel):
    """Single direct usage item for a Callback."""

    io_name: str
    iport_name: str


class IndirectCallbackUsageItem(BaseModel):
    """Single indirect usage item for a Callback."""

    flow_name: str
    node_instance_name: str


class NodeFlowUsage(BaseModel):
    """Usage details for a Node in a specific Flow.

    Can have both direct and indirect usages.
    """

    direct: List[DirectNodeUsageItem] = Field(default_factory=list)
    indirect: List[IndirectNodeUsageItem] = Field(default_factory=list)


class FlowFlowUsage(BaseModel):
    """Usage details for a Flow in a specific parent Flow.

    Can have both direct and indirect usages.
    """

    direct: List[DirectFlowUsageItem] = Field(default_factory=list)
    indirect: List[IndirectFlowUsageItem] = Field(default_factory=list)


class CallbackNodeUsage(BaseModel):
    """Usage details for a Callback in a specific Node.

    Indirect usages may be applicable if the Callback is used in a Node that is part of a Flow.
    """

    direct: List[DirectCallbackUsageItem] = Field(default_factory=list)
    indirect: List[IndirectCallbackUsageItem] = Field(default_factory=list)


class UsageData(BaseModel):
    """Usage data that can represent both Node and Flow usage."""

    flow: Dict[str, Union[NodeFlowUsage, FlowFlowUsage]] = Field(default_factory=dict)
    node: Dict[str, Union[NodeFlowUsage, FlowFlowUsage, CallbackNodeUsage]] = Field(
        default_factory=dict
    )


class UsageSearchResult(BaseModel):
    """Result structure for usage search.

    Format:
    {
        "scope": "Node" | "Flow" | "Callback",
        "name": "object_name",
        "usage": {
            "flow": {
                "flow_name": {
                    "direct": [...],
                    "indirect": [...]
                }
            },
            "node": {
                "node_name": {
                    "direct": [...],
                    "indirect": [...]
                },
                "callback_name": {
                    "direct": [...],
                }
            }
        }
    }
    """

    scope: str  # "Node" or "Flow" or "Callback"
    name: str  # Name of the object being searched
    usage: UsageData  # Can contain both flow and node usage
