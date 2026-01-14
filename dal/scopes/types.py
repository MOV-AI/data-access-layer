"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Type definitions for scope classes.
"""
from typing import List, Optional, TypedDict


class PathElement(TypedDict):
    """Represents an element in the usage path of a Node or Flow instance.

    Used to track the chain from a top-level flow down to a specific node instance,
    showing each container/subflow traversed along the way.
    """

    flow: str
    Container: Optional[str]  # Present when traversing through a container/subflow
    NodeInst: Optional[str]  # Present at the final element (the actual node instance)


class NodeUsageInfo(TypedDict):
    """Represents usage information of a Node instance in flows.

    Attributes:
        flow: Name of the flow containing the node instance
        NodeInst: Name of the node instance
        direct: True if the node is directly in the flow, False if indirect (via subflow)
        path: Chain of flows/containers leading to this usage (only present when direct=False)
    """

    flow: str
    NodeInst: str
    direct: bool
    path: Optional[List[PathElement]]  # Only present when direct is False


class FlowUsageInfo(TypedDict):
    """Represents usage information of a Flow as a subflow in other flows.

    Attributes:
        flow: Name of the parent flow that uses this flow as a subflow
        Container: Name of the container instance
        direct: True if directly used, False if indirect (parent is also a subflow)
        path: Chain of flows/containers leading to this usage (only present when direct=False)
    """

    flow: str
    Container: str
    direct: bool
    path: Optional[List[PathElement]]  # Only present when direct is False
