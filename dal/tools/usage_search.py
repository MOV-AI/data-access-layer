import json

from movai_core_shared.exceptions import DoesNotExist
from dal.utils.usage_search.usage_types import UsageSearchResult, UsageData
from dal.utils import get_usage_search_scope_map


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
        scope_type = result.scope
        obj_name = result.name
        usage: UsageData = result.usage

        direct_count = sum(
            len(details["direct"])
            for usage_type in usage.model_dump().values()
            for details in usage_type.values()
        )
        indirect_count = sum(
            len(details["indirect"])
            for usage_type in usage.model_dump().values()
            for details in usage_type.values()
        )
        # Count total usages across all scope types
        total_count = direct_count + indirect_count

        if total_count == 0:
            print(f"{scope_type} '{obj_name}' is not used anywhere.")
            return

        print(f"\n{scope_type} '{obj_name}' is used in {total_count} location(s):")
        print("-" * 80)

        # Iterate through each scope type (e.g., "Flow")
        for parent_scope, parent_items in usage.model_dump().items():
            for parent_name, details in parent_items.items():
                # Handle direct usages
                direct_items = details["direct"]
                for direct_item in direct_items:
                    if scope_type == "Node":
                        instance = direct_item["node_instance_name"]
                        print(f"  [Direct] {parent_scope}: {parent_name}")
                        print(f"           Node Instance: {instance}")
                    elif scope_type == "Flow":
                        instance = direct_item["flow_instance_name"]
                        print(f"  [Direct] {parent_scope}: {parent_name}")
                        print(f"           Flow Instance (Container): {instance}")

                # Handle indirect usages
                indirect_items = details["indirect"]
                for indirect_item in indirect_items:
                    child_template = indirect_item["flow_template_name"]
                    child_instance = indirect_item["flow_instance_name"]
                    print(f"  [Indirect] {parent_scope}: {parent_name}")
                    print(f"           As Sub Flow: {child_template} (instance: {child_instance})")

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
        scope_map = get_usage_search_scope_map()

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
