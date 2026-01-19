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


class UsageData(BaseModel):
    """Usage data that can represent both Node and Flow usage."""

    flow: Dict[str, Union[NodeFlowUsage, FlowFlowUsage]] = Field(default_factory=dict)
    node: Dict[str, Union[NodeFlowUsage, FlowFlowUsage]] = Field(default_factory=dict)


class UsageSearchResult(BaseModel):
    """Result structure for usage search.

    Format:
    {
        "scope": "Node" | "Flow",
        "name": "object_name",
        "usage": {
            "flow": {
                "flow_name": {
                    "direct": [...],
                    "indirect": [...]
                }
            }
        }
    }
    """

    scope: str  # "Node" or "Flow"
    name: str  # Name of the object being searched
    usage: UsageData  # Can contain both flow and node usage
