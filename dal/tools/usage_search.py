import json

from movai_core_shared.exceptions import DoesNotExist

from dal.scopes.flow import Flow
from dal.scopes.node import Node


SCOPE_MAP = {
    "node": Node,
    "flow": Flow,
}


class Searcher:
    """Search for node and flow usage across the system."""

    def __init__(self, debug: bool = False):
        """Initialize the Searcher.

        Args:
            debug (bool): Enable debug output
        """
        self.debug = debug

    def print_results(self, obj_name: str, usage: list, search_type: str):
        """Print search results in a readable format.

        Args:
            result (dict): Search result from search_node or search_flow
            search_type (str): Either "node" or "flow"
        """

        if not usage:
            print(f"{search_type.capitalize()} '{obj_name}' is not used in any flows.")
            return

        print(f"\n{search_type.capitalize()} '{obj_name}' is used in {len(usage)} flow(s):")
        print("-" * 60)

        for item in usage:
            flow = item.get("flow")
            direct = item.get("direct", True)
            status = "Direct" if direct else "Indirect"
            path = item.get("path", None)

            if search_type == "node":
                node_inst = item.get("NodeInst")
                if path:
                    path = " -> ".join(str(p) for p in path)
                    print(f"  [{status}] Flow: {flow}, NodeInst: {node_inst}, \n\tPath: {path}")
                else:
                    print(f"  [{status}] Flow: {flow}, NodeInst: {node_inst}")
            else:  # flow
                container = item.get("Container")
                if path:
                    path = " -> ".join(str(p) for p in path)
                    print(f"  [{status}] Flow: {flow}, Container: {container}, \n\tPath: {path}")
                else:
                    print(f"  [{status}] Flow: {flow}, Container: {container}")

        print()

        if self.debug:
            print("\nFull JSON result:")
            print(json.dumps(usage, indent=2))

    def search_usage(self, search_type: str, name: str) -> int:
        """Search for usage of a node or flow.

        Args:
            search_type (str): Either "node" or "flow"
            name (str): Name of the node or flow to search for

        Returns:
            int: Exit code (0 for success, 1 for failure)

        """
        try:
            scope = SCOPE_MAP[search_type](name)
        except DoesNotExist:
            print(f"{search_type.capitalize()} '{name}' does not exist.")
            return 1

        usage = scope.get_usage_info()

        self.print_results(name, usage, search_type)

        return 0
