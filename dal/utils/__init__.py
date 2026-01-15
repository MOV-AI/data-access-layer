"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Utility modules for DAL.
"""
from .usage_search.types import (
    UsageSearchResult,
    DirectNodeUsageItem,
    IndirectNodeUsageItem,
    DirectFlowUsageItem,
    IndirectFlowUsageItem,
    NodeFlowUsage,
    FlowFlowUsage,
)


# Lazy import to avoid circular dependency
def get_usage_search_scope_map():
    """Get the mapping of scope types that support usage search.

    This is a re-export with lazy loading to avoid circular imports.
    """
    from .usage_search.scope_map import get_usage_search_scope_map as _get_map

    return _get_map()


__all__ = [
    "UsageSearchResult",
    "DirectNodeUsageItem",
    "IndirectNodeUsageItem",
    "DirectFlowUsageItem",
    "IndirectFlowUsageItem",
    "NodeFlowUsage",
    "FlowFlowUsage",
    "get_usage_search_scope_map",
]
