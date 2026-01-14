"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Usage search scope mapping utilities.
"""
from typing import TYPE_CHECKING, Dict, Optional, Type, List, TypedDict

if TYPE_CHECKING:
    from dal.scopes.scope import Scope


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


def get_usage_search_scope_map() -> Dict[str, Type["Scope"]]:
    """Get the mapping of scope types that support usage search.

    This function uses lazy imports to avoid circular dependencies.

    Returns:
        Dict[str, Type[Scope]]: Mapping of type names to scope classes
            that implement get_usage_info() method.
    """
    from dal.scopes.node import Node
    from dal.scopes.flow import Flow

    return {
        "node": Node,
        "flow": Flow,
    }


class _UsageSearchScopeMapCache:
    """Cache holder for usage search scope map using descriptor pattern."""

    _cache: Optional[Dict[str, Type["Scope"]]] = None

    @classmethod
    def get(cls) -> Dict[str, Type["Scope"]]:
        """Get cached version of usage search scope map.

        Returns:
            Dict[str, Type[Scope]]: Cached mapping of type names to scope classes.
        """
        if cls._cache is None:
            cls._cache = get_usage_search_scope_map()
        return cls._cache


def get_cached_usage_search_scope_map() -> Dict[str, Type["Scope"]]:
    """Get cached version of usage search scope map.

    Returns:
        Dict[str, Type[Scope]]: Cached mapping of type names to scope classes.
    """
    return _UsageSearchScopeMapCache.get()
