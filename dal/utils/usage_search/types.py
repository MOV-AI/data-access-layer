"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Usage search scope mapping utilities.
"""
from typing import Dict, Any, TypedDict, List


class DirectNodeUsageItem(TypedDict):
    """Single direct usage item for a Node."""

    node_instance_name: str


class IndirectNodeUsageItem(TypedDict):
    """Single indirect usage item for a Node - references immediate child flow."""

    flow_template_name: str
    flow_instance_name: str


class DirectFlowUsageItem(TypedDict):
    """Single direct usage item for a Flow."""

    flow_instance_name: str


class IndirectFlowUsageItem(TypedDict):
    """Single indirect usage item for a Flow - references immediate child flow."""

    flow_template_name: str
    flow_instance_name: str


class NodeFlowUsage(TypedDict, total=False):
    """Usage details for a Node in a specific Flow.

    Can have both direct and indirect usages.
    """

    direct: List[DirectNodeUsageItem]
    indirect: List[IndirectNodeUsageItem]


class FlowFlowUsage(TypedDict, total=False):
    """Usage details for a Flow in a specific parent Flow.

    Can have both direct and indirect usages.
    """

    direct: List[DirectFlowUsageItem]
    indirect: List[IndirectFlowUsageItem]


class UsageSearchResult(TypedDict):
    """Result structure for usage search.

    Format:
    {
        "scope": "Node" | "Flow",
        "name": "object_name",
        "usage": {
            "Flow": {
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
    usage: Dict[str, Dict[str, Any]]  # Nested dict: scope_type -> parent_name -> usage_details
