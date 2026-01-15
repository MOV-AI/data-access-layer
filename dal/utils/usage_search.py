"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Usage search scope mapping utilities.
"""
from typing import TYPE_CHECKING, Dict, Optional, Type, Any, TypedDict, List

if TYPE_CHECKING:
    from dal.scopes.scope import Scope


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
