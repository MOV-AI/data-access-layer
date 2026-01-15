"""Tests for Node and Flow classmethod usage search functionality."""
from movai_core_shared.exceptions import DoesNotExist

from dal.utils.usage_search import get_usage_search_scope_map, UsageSearchResult


def get_scope_instance(search_type, name):
    """Helper to get scope instance based on type and name."""
    try:
        scope = get_usage_search_scope_map()[search_type](name)
    except DoesNotExist as e:
        print(f"{search_type.capitalize()} '{name}' does not exist.")
        raise e
    return scope


class TestNodeUsageInfo:
    """Test suite for Node.get_usage_info() classmethod."""

    def test_node_get_usage_info(self, setup_test_data):
        """
        Test Node.get_usage_info() with recursive search.

        Test scenario:
        - NodeSub1 is used directly in every flow (twice in flow_with_duplicated_subflow)
        - flow_with_four_nodes is a subflow in flow_with_duplicated_subflow
        - flow_with_duplicated_subflow is a subflow in flow_with_nodes_and_subflow
        - Therefore NodeSub1 should appear with both direct and indirect usages
        """

        node = get_scope_instance("node", "NodeSub1")
        result: UsageSearchResult = node.get_usage_info()

        expected_result = UsageSearchResult(
            scope="Node",
            name="NodeSub1",
            usage={
                "Flow": {
                    "flow_not_used_as_subflow": {
                        "direct": [{"node_instance_name": "sub"}],
                        "indirect": [],
                    },
                    "flow_with_duplicated_subflow": {
                        "direct": [
                            {"node_instance_name": "sub1"},
                            {"node_instance_name": "sub2"},
                        ],
                        "indirect": [
                            {
                                "flow_template_name": "flow_with_four_nodes",
                                "flow_instance_name": "subflow1",
                            },
                            {
                                "flow_template_name": "flow_with_four_nodes",
                                "flow_instance_name": "subflow2",
                            },
                        ],
                    },
                    "flow_with_four_nodes": {
                        "direct": [{"node_instance_name": "nodesub1"}],
                        "indirect": [],
                    },
                    "flow_with_nodes_and_subflow": {
                        "direct": [{"node_instance_name": "sub"}],
                        "indirect": [
                            {
                                "flow_template_name": "flow_with_duplicated_subflow",
                                "flow_instance_name": "subflow",
                            }
                        ],
                    },
                }
            },
        )
        assert result == expected_result

    def test_node_get_usage_info_multiple_calls(self, setup_test_data):
        """
        Test that Node.get_usage_info() can be called multiple times without instantiation.

        Test scenario:
        - NodeSub1 is used directly in every flow and twice in flow_with_duplicated_subflow
        - NodeSub1 is indirectly referenced via flow_with_duplicated_subflow twice
             and once in flow_with_nodes_and_subflow
        - NodeSub2 is used directly in flow_with_four_nodes
        - NodeSub2 is indirectly referenced via flow_with_duplicated_subflow twice
            and once in flow_with_nodes_and_subflow
        - NodePub1 is directly used once in every flow
        - NodePub1 is indirectly referenced via flow_with_duplicated_subflow twice
            and once in flow_with_nodes_and_subflow

        """

        # Call multiple times for different nodes
        node1 = get_scope_instance("node", "NodeSub1")
        node2 = get_scope_instance("node", "NodeSub2")
        node3 = get_scope_instance("node", "NodePub1")

        result1 = node1.get_usage_info()
        result2 = node2.get_usage_info()
        result3 = node3.get_usage_info()

        # Each should have independent results
        # Count total usages across all scopes (direct + indirect)
        def count_usages(result):
            return sum(
                len(details.get("direct", [])) + len(details.get("indirect", []))
                for items in result["usage"].values()
                for details in items.values()
            )

        total1 = count_usages(result1)
        total2 = count_usages(result2)
        total3 = count_usages(result3)

        # NodeSub1: 5 direct in 4 flows + 3 indirect = 8
        # NodeSub2: 1 direct in flow_with_four_nodes + 3 indirect = 4
        # NodePub1: 4 direct in 4 flows + 3 indirect = 7
        assert total1 == 8
        assert total2 == 4
        assert total3 == 7

    def test_unused_node_get_usage_info(self, setup_test_data):
        """Test Node.get_usage_info() for a node that is not used in any flow."""

        node = get_scope_instance("node", "UnusedNode")
        result: UsageSearchResult = node.get_usage_info()

        expected_result = UsageSearchResult(scope="Node", name="UnusedNode", usage={"Flow": {}})
        assert result == expected_result


class TestFlowUsageInfo:
    """Test suite for Flow.get_usage_info() classmethod."""

    def test_flow_get_usage_info_not_used_as_subflow(self, setup_test_data):
        """Test Flow.get_usage_info() for a flow that is not used as a subflow."""

        # Test flow_not_used_as_subflow usage (not used as subflow anywhere)
        flow = get_scope_instance("flow", "flow_not_used_as_subflow")
        usage = flow.get_usage_info()

        assert len(usage) == 0

    def test_flow_get_usage_info(self, setup_test_data):
        """
        Test Flow.get_usage_info() with recursive search.

        Test scenario:
        - flow_with_four_nodes is directly used in flow_with_duplicated_subflow
        - flow_with_duplicated_subflow is directly used in flow_with_nodes_and_subflow
        - Therefore flow_with_four_nodes should appear:
          - Directly in flow_with_duplicated_subflow
          - Indirectly in flow_with_nodes_and_subflow (via flow_with_duplicated_subflow)
        """

        flow = get_scope_instance("flow", "flow_with_four_nodes")
        usage = flow.get_usage_info()

        # Should have both direct and indirect usages
        direct_usages = [item for item in usage if item.get("direct", True)]
        indirect_usages = [item for item in usage if not item.get("direct", True)]

        # Direct usage: flow_with_duplicated_subflow (twice as subflow1 and subflow2)
        assert len(direct_usages) == 2
        assert {
            "flow": "flow_with_duplicated_subflow",
            "Container": "subflow1",
            "direct": True,
        } in direct_usages
        assert {
            "flow": "flow_with_duplicated_subflow",
            "Container": "subflow2",
            "direct": True,
        } in direct_usages

        # Indirect usages should exist (flow_with_nodes_and_subflow via flow_with_duplicated_subflow)
        assert len(indirect_usages) >= 1

        # Verify indirect usages have paths
        for item in indirect_usages:
            assert "path" in item
            assert isinstance(item["path"], list)
            assert len(item["path"]) >= 2  # At least 2 hops in the path

    def test_flow_get_usage_info_nested_subflow(self, setup_test_data):
        """Test Flow.get_usage_info() for flow_with_duplicated_subflow which is used in flow_with_nodes_and_subflow."""

        flow = get_scope_instance("flow", "flow_with_duplicated_subflow")
        usage = flow.get_usage_info()

        assert len(usage) == 1

        usage = usage[0]
        assert usage["flow"] == "flow_with_nodes_and_subflow"
        assert usage["Container"] == "subflow"
        assert usage["direct"] is True

    def test_flow_get_usage_info_multiple_calls(self, setup_test_data):
        """Test that Flow.get_usage_info() can be called multiple times without instantiation."""

        # Call multiple times for different flows
        flow1 = get_scope_instance("flow", "flow_with_four_nodes")
        flow2 = get_scope_instance("flow", "flow_not_used_as_subflow")
        flow3 = get_scope_instance("flow", "flow_with_duplicated_subflow")

        usage1 = flow1.get_usage_info()
        usage2 = flow2.get_usage_info()
        usage3 = flow3.get_usage_info()

        print(len(usage1), len(usage2), len(usage3))

        # Each should have independent results
        assert len(usage1) == 4
        assert len(usage2) == 0
        assert len(usage3) == 1
