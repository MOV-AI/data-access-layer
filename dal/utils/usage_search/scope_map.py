from typing import Dict, Type

from dal.scopes.scope import Scope
from dal.scopes.node import Node
from dal.scopes.flow import Flow


def get_usage_search_scope_map() -> Dict[str, Type[Scope]]:
    """Get the mapping of scope types that support usage search.

    Returns:
        Dict[str, Type[Scope]]: Mapping of type names to scope classes
            that implement get_usage_info() method.
    """

    return {
        "node": Node,
        "flow": Flow,
    }
