import json
import sys


class Searcher:
    """Search for node and flow usage across the system."""

    def __init__(self, debug: bool = False):
        """Initialize the Searcher.

        Args:
            debug (bool): Enable debug output
        """
        self.debug = debug

    def search_node_usage(self, node_name: str, recursive: bool = False) -> dict:
        """Search for node usage across flows.

        Args:
            node_name (str): Name of the node to search for
            recursive (bool): If True, include indirect usage through subflows

        Returns:
            dict: Usage information with structure:
                {
                    "node": str,
                    "usage": List[dict],
                    "error": str (optional)
                }
        """
        from dal.scopes.node import Node

        if self.debug:
            print(f"Searching for node '{node_name}' (recursive={recursive})")

        return Node.get_usage_info(node_name, recursive=recursive)

    def search_flow_usage(self, flow_name: str, recursive: bool = False) -> dict:
        """Search for flow usage as a subflow across other flows.

        Args:
            flow_name (str): Name of the flow to search for
            recursive (bool): If True, include indirect usage through nested subflows

        Returns:
            dict: Usage information with structure:
                {
                    "flow": str,
                    "usage": List[dict],
                    "error": str (optional)
                }
        """
        from dal.scopes.flow import Flow

        if self.debug:
            print(f"Searching for flow '{flow_name}' (recursive={recursive})")

        return Flow.get_usage_info(flow_name, recursive=recursive)

    def print_results(self, result: dict, search_type: str):
        """Print search results in a readable format.

        Args:
            result (dict): Search result from search_node or search_flow
            search_type (str): Either "node" or "flow"
        """

        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            return

        obj_name = result.get(search_type)
        usage = result.get("usage", [])

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
            print(json.dumps(result, indent=2))
