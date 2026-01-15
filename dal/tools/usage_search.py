import json

from movai_core_shared.exceptions import DoesNotExist
from dal.utils.usage_search import get_cached_usage_search_scope_map, UsageSearchResult


class Searcher:
    """Search for node and flow usage across the system."""

    def __init__(self, debug: bool = False):
        """Initialize the Searcher.

        Args:
            debug (bool): Enable debug output
        """
        self.debug = debug

    def print_results(self, result: UsageSearchResult):
        """Print search results in a readable format.

        Args:
            result (UsageSearchResult): Search result from get_usage_info()
        """
        scope_type = result["scope"]
        obj_name = result["name"]
        usage = result["usage"]

        direct_count = sum(
            len(details.get("direct", []))
            for parent_items in usage.values()
            for details in parent_items.values()
        )
        indirect_count = sum(
            len(details.get("indirect", []))
            for parent_items in usage.values()
            for details in parent_items.values()
        )
        # Count total usages across all scope types
        total_count = direct_count + indirect_count

        if total_count == 0:
            print(f"{scope_type} '{obj_name}' is not used anywhere.")
            return

        print(f"\n{scope_type} '{obj_name}' is used in {total_count} location(s):")
        print("-" * 80)

        # Iterate through each scope type (e.g., "Flow")
        for parent_scope, parent_items in usage.items():
            for parent_name, details in parent_items.items():
                # Handle direct usages
                direct_items = details.get("direct", [])
                for direct_item in direct_items:
                    if scope_type == "Node":
                        instance = direct_item.get("node_instance_name", "N/A")
                        print(f"  [Direct] {parent_scope}: {parent_name}")
                        print(f"           Node Instance: {instance}")
                    elif scope_type == "Flow":
                        instance = direct_item.get("flow_instance_name", "N/A")
                        print(f"  [Direct] {parent_scope}: {parent_name}")
                        print(f"           Flow Instance (Container): {instance}")

                # Handle indirect usages
                indirect_items = details.get("indirect", [])
                for indirect_item in indirect_items:
                    child_template = indirect_item.get("flow_template_name", "N/A")
                    child_instance = indirect_item.get("flow_instance_name", "N/A")
                    print(f"  [Indirect] {parent_scope}: {parent_name}")
                    print(
                        f"           Via Child Flow: {child_template} (instance: {child_instance})"
                    )

        print()

        if self.debug:
            print("\nFull JSON result:")
            print(json.dumps(result, indent=2, default=str))

    def search_usage(self, search_type: str, name: str) -> int:
        """Search for usage of a node or flow.

        Args:
            search_type (str): Either "node" or "flow"
            name (str): Name of the node or flow to search for

        Returns:
            int: Exit code (0 for success, 1 for failure)

        """
        scope_map = get_cached_usage_search_scope_map()

        try:
            scope = scope_map.get(search_type, None)
            if scope is None:
                print(f"Invalid type parameter. Must be one of {list(scope_map.keys())}.")
                return 1
            obj = scope(name)
        except DoesNotExist:
            print(f"{search_type.capitalize()} '{name}' does not exist.")
            return 1

        result = obj.get_usage_info()

        self.print_results(result)

        return 0
