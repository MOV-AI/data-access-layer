"""Tests for Node and Flow classmethod usage search functionality."""
from movai_core_shared.exceptions import DoesNotExist

from dal.utils import UsageSearchResult, get_usage_search_scope_map


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
        result: UsageSearchResult = flow.get_usage_info()

        expected_result = UsageSearchResult(
            scope="Flow", name="flow_not_used_as_subflow", usage={"Flow": {}}
        )
        assert result == expected_result

    def test_flow_get_usage_info_nested_subflow(self, setup_test_data):
        """
        Test Flow.get_usage_info() for flow_with_duplicated_subflow
        which is used in flow_with_nodes_and_subflow.

        Test scenario:
        - flow_with_duplicated_subflow is directly used in flow_with_nodes_and_subflow

        """

        flow = get_scope_instance("flow", "flow_with_duplicated_subflow")
        result: UsageSearchResult = flow.get_usage_info()

        expected_result = UsageSearchResult(
            scope="Flow",
            name="flow_with_duplicated_subflow",
            usage={
                "Flow": {
                    "flow_with_nodes_and_subflow": {
                        "direct": [{"flow_instance_name": "subflow"}],
                        "indirect": [],
                    }
                }
            },
        )
        assert result == expected_result

    def test_flow_get_usage_info(self, setup_test_data):
        """
        Test Flow.get_usage_info() for flow_with_four_nodes which is used in other flows.

        Test scenario:
        - flow_with_four_nodes is directly used in flow_with_duplicated_subflow
            (twice: subflow1 and subflow2)
        - flow_with_duplicated_subflow is directly used in flow_with_nodes_and_subflow
        - Therefore flow_with_four_nodes should appear:
          - Directly in flow_with_duplicated_subflow (with both instances)
          - Indirectly in flow_with_nodes_and_subflow (via flow_with_duplicated_subflow)
        """

        flow = get_scope_instance("flow", "flow_with_four_nodes")
        result: UsageSearchResult = flow.get_usage_info()

        expected_result = UsageSearchResult(
            scope="Flow",
            name="flow_with_four_nodes",
            usage={
                "Flow": {
                    "flow_with_duplicated_subflow": {
                        "direct": [
                            {"flow_instance_name": "subflow1"},
                            {"flow_instance_name": "subflow2"},
                        ],
                        "indirect": [],
                    },
                    "flow_with_nodes_and_subflow": {
                        "direct": [],
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

    def test_flow_get_usage_info_multiple_calls(self, setup_test_data):
        """
        Test that Flow.get_usage_info() can be called multiple times independently.

        Test scenario:
        - flow_with_four_nodes is used directly in flow_with_duplicated_subflow (twice)
            and indirectly in flow_with_nodes_and_subflow
        - flow_not_used_as_subflow is not used anywhere
        - flow_with_duplicated_subflow is used directly in flow_with_nodes_and_subflow

        """

        # Call multiple times for different flows
        flow1 = get_scope_instance("flow", "flow_with_four_nodes")
        flow2 = get_scope_instance("flow", "flow_not_used_as_subflow")
        flow3 = get_scope_instance("flow", "flow_with_duplicated_subflow")

        result1 = flow1.get_usage_info()
        result2 = flow2.get_usage_info()
        result3 = flow3.get_usage_info()

        # Count total usages (direct + indirect)
        def count_usages(result):
            return sum(
                len(details.get("direct", [])) + len(details.get("indirect", []))
                for items in result["usage"].values()
                for details in items.values()
            )

        total1 = count_usages(result1)
        total2 = count_usages(result2)
        total3 = count_usages(result3)

        # flow_with_four_nodes: 2 direct in flow_with_duplicated_subflow
        #     + 1 indirect in flow_with_nodes_and_subflow = 3
        # flow_not_used_as_subflow: 0
        # flow_with_duplicated_subflow: 1 direct in flow_with_nodes_and_subflow = 1
        assert total1 == 3
        assert total2 == 0
        assert total3 == 1


class TestCircularDependencyHandling:
    """Test suite for circular dependency handling in usage search algorithm."""

    def test_node_circular_dependency_prevention(self, circular_dependency_data):
        """
        Test that Node._find_all_indirect_usages handles circular dependencies correctly.

        Uses flow_circular_a <-> flow_circular_b with TestNodeCircular in flow_circular_a.
        """
        from dal.scopes.node import Node
        import time

        # Get usage info - this should NOT cause infinite loop
        start_time = time.time()

        node = Node("TestNodeCircular")
        result = node.get_usage_info()

        elapsed_time = time.time() - start_time

        # Verify it completed quickly (no infinite loop)
        assert elapsed_time < 2.0, f"Algorithm took {elapsed_time:.2f}s, possible infinite loop"

        # Verify results structure
        expected_result = UsageSearchResult(
            scope="Node",
            name="TestNodeCircular",
            usage={
                "Flow": {
                    "flow_circular_a": {
                        "direct": [{"node_instance_name": "test_node"}],
                        "indirect": [
                            {
                                "flow_template_name": "flow_circular_b",
                                "flow_instance_name": "container_to_b",
                            }
                        ],
                    },
                    "flow_circular_b": {
                        "direct": [],
                        "indirect": [
                            {
                                "flow_template_name": "flow_circular_a",
                                "flow_instance_name": "container_to_a",
                            }
                        ],
                    },
                }
            },
        )
        assert result == expected_result

    def test_flow_circular_dependency_prevention(self, circular_dependency_data):
        """
        Test that Flow._find_all_indirect_usages handles circular dependencies correctly.

        Uses flow_circular_x <-> flow_circular_y mutual container references.
        """
        from dal.scopes.flow import Flow
        import time

        # Test flow_circular_x usage
        start_time = time.time()

        flow_x = Flow("flow_circular_x")
        result_x = flow_x.get_usage_info()

        elapsed_time = time.time() - start_time

        # Verify it completed quickly
        assert elapsed_time < 2.0, f"Algorithm took {elapsed_time:.2f}s, possible infinite loop"

        # flow_circular_x should be used in flow_circular_y
        expected_result_x = UsageSearchResult(
            scope="Flow",
            name="flow_circular_x",
            usage={
                "Flow": {
                    "flow_circular_y": {
                        "direct": [{"flow_instance_name": "container_to_x"}],
                        "indirect": [
                            {
                                "flow_template_name": "flow_circular_x",
                                "flow_instance_name": "container_to_x",
                            }
                        ],
                    },
                    "flow_circular_x": {
                        "direct": [],
                        "indirect": [
                            {
                                "flow_template_name": "flow_circular_y",
                                "flow_instance_name": "container_to_y",
                            }
                        ],
                    },
                }
            },
        )
        assert result_x == expected_result_x

        # Test flow_circular_y usage
        flow_y = Flow("flow_circular_y")
        result_y = flow_y.get_usage_info()

        # flow_circular_y should be used in flow_circular_x
        expected_result_y = UsageSearchResult(
            scope="Flow",
            name="flow_circular_y",
            usage={
                "Flow": {
                    "flow_circular_x": {
                        "direct": [{"flow_instance_name": "container_to_y"}],
                        "indirect": [
                            {
                                "flow_template_name": "flow_circular_y",
                                "flow_instance_name": "container_to_y",
                            }
                        ],
                    },
                    "flow_circular_y": {
                        "direct": [],
                        "indirect": [
                            {
                                "flow_template_name": "flow_circular_x",
                                "flow_instance_name": "container_to_x",
                            }
                        ],
                    },
                }
            },
        )
        assert result_y == expected_result_y

    def test_multi_level_circular_dependency(self, circular_dependency_data):
        """
        Test circular dependency with 3 flows: A -> B -> C -> A

        Uses flow_multi_a -> flow_multi_b -> flow_multi_c -> flow_multi_a
        with TestNodeMultiCircular in flow_multi_a.
        """
        from dal.scopes.node import Node
        import time

        start_time = time.time()

        node = Node("TestNodeMultiCircular")
        result = node.get_usage_info()

        elapsed_time = time.time() - start_time

        # Verify it completed quickly (no infinite loop)
        assert elapsed_time < 2.0, f"Algorithm took {elapsed_time:.2f}s, possible infinite loop"

        # Verify structure
        expected_result = UsageSearchResult(
            scope="Node",
            name="TestNodeMultiCircular",
            usage={
                "Flow": {
                    "flow_multi_a": {
                        "direct": [{"node_instance_name": "test_node"}],
                        "indirect": [
                            {
                                "flow_template_name": "flow_multi_b",
                                "flow_instance_name": "container_to_b",
                            }
                        ],
                    },
                    "flow_multi_b": {
                        "direct": [],
                        "indirect": [
                            {
                                "flow_template_name": "flow_multi_c",
                                "flow_instance_name": "container_to_c",
                            }
                        ],
                    },
                    "flow_multi_c": {
                        "direct": [],
                        "indirect": [
                            {
                                "flow_template_name": "flow_multi_a",
                                "flow_instance_name": "container_to_a",
                            }
                        ],
                    },
                }
            },
        )
        assert result == expected_result
