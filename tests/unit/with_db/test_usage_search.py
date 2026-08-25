"""Tests for Node and Flow classmethod usage search functionality."""
from movai_core_shared.exceptions import DoesNotExist

from dal.utils.usage_search.usage_types import (
    UsageData,
    UsageSearchResult,
    NodeFlowUsage,
    FlowFlowUsage,
    CallbackNodeUsage,
    DirectNodeUsageItem,
    DirectFlowUsageItem,
    IndirectNodeUsageItem,
    IndirectFlowUsageItem,
    DirectCallbackUsageItem,
    IndirectCallbackUsageItem,
)
from dal.utils.usage_search.scope_map import get_usage_search_scope_map


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
            usage=UsageData(
                flow={
                    "flow_not_used_as_subflow": NodeFlowUsage(
                        direct=[DirectNodeUsageItem(node_instance_name="sub")],
                        indirect=[],
                    ),
                    "flow_with_duplicated_subflow": NodeFlowUsage(
                        direct=[
                            DirectNodeUsageItem(node_instance_name="sub1"),
                            DirectNodeUsageItem(node_instance_name="sub2"),
                        ],
                        indirect=[
                            IndirectNodeUsageItem(
                                flow_template_name="flow_with_four_nodes",
                                flow_instance_name="subflow1",
                            ),
                            IndirectNodeUsageItem(
                                flow_template_name="flow_with_four_nodes",
                                flow_instance_name="subflow2",
                            ),
                        ],
                    ),
                    "flow_with_four_nodes": NodeFlowUsage(
                        direct=[DirectNodeUsageItem(node_instance_name="nodesub1")],
                        indirect=[],
                    ),
                    "flow_with_nodes_and_subflow": NodeFlowUsage(
                        direct=[DirectNodeUsageItem(node_instance_name="sub")],
                        indirect=[
                            IndirectNodeUsageItem(
                                flow_template_name="flow_with_duplicated_subflow",
                                flow_instance_name="subflow",
                            )
                        ],
                    ),
                }
            ),
        )
        # Use model_dump() for comparison to avoid Pydantic equality issues
        assert result.model_dump() == expected_result.model_dump()

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
            total = 0
            if result.usage.flow:
                for flow_usage in result.usage.flow.values():
                    total += len(flow_usage.direct) + len(flow_usage.indirect)
            if result.usage.node:
                for node_usage in result.usage.node.values():
                    total += len(node_usage.direct) + len(node_usage.indirect)
            return total

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

        expected_result = UsageSearchResult(
            scope="Node", name="UnusedNode", usage=UsageData(flow={})
        )
        assert result.model_dump() == expected_result.model_dump()


class TestFlowUsageInfo:
    """Test suite for Flow.get_usage_info() classmethod."""

    def test_flow_get_usage_info_not_used_as_subflow(self, setup_test_data):
        """Test Flow.get_usage_info() for a flow that is not used as a subflow."""

        # Test flow_not_used_as_subflow usage (not used as subflow anywhere)
        flow = get_scope_instance("flow", "flow_not_used_as_subflow")
        result: UsageSearchResult = flow.get_usage_info()

        expected_result = UsageSearchResult(
            scope="Flow", name="flow_not_used_as_subflow", usage=UsageData(flow={})
        )
        assert result.model_dump() == expected_result.model_dump()

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
            usage=UsageData(
                flow={
                    "flow_with_nodes_and_subflow": FlowFlowUsage(
                        direct=[DirectFlowUsageItem(flow_instance_name="subflow")],
                        indirect=[],
                    )
                }
            ),
        )
        assert result.model_dump() == expected_result.model_dump()

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
            usage=UsageData(
                flow={
                    "flow_with_duplicated_subflow": FlowFlowUsage(
                        direct=[
                            DirectFlowUsageItem(flow_instance_name="subflow1"),
                            DirectFlowUsageItem(flow_instance_name="subflow2"),
                        ],
                        indirect=[],
                    ),
                    "flow_with_nodes_and_subflow": FlowFlowUsage(
                        direct=[],
                        indirect=[
                            IndirectFlowUsageItem(
                                flow_template_name="flow_with_duplicated_subflow",
                                flow_instance_name="subflow",
                            )
                        ],
                    ),
                }
            ),
        )
        assert result.model_dump() == expected_result.model_dump()

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
            total = 0
            if result.usage.flow:
                for flow_usage in result.usage.flow.values():
                    total += len(flow_usage.direct) + len(flow_usage.indirect)
            if result.usage.node:
                for node_usage in result.usage.node.values():
                    total += len(node_usage.direct) + len(node_usage.indirect)
            return total

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
            usage=UsageData(
                flow={
                    "flow_circular_a": NodeFlowUsage(
                        direct=[DirectNodeUsageItem(node_instance_name="test_node")],
                        indirect=[
                            IndirectNodeUsageItem(
                                flow_template_name="flow_circular_b",
                                flow_instance_name="container_to_b",
                            )
                        ],
                    ),
                    "flow_circular_b": NodeFlowUsage(
                        direct=[],
                        indirect=[
                            IndirectNodeUsageItem(
                                flow_template_name="flow_circular_a",
                                flow_instance_name="container_to_a",
                            )
                        ],
                    ),
                }
            ),
        )
        assert result.model_dump() == expected_result.model_dump()

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
            usage=UsageData(
                flow={
                    "flow_circular_y": FlowFlowUsage(
                        direct=[DirectFlowUsageItem(flow_instance_name="container_to_x")],
                        indirect=[
                            IndirectFlowUsageItem(
                                flow_template_name="flow_circular_x",
                                flow_instance_name="container_to_x",
                            )
                        ],
                    ),
                    "flow_circular_x": FlowFlowUsage(
                        direct=[],
                        indirect=[
                            IndirectFlowUsageItem(
                                flow_template_name="flow_circular_y",
                                flow_instance_name="container_to_y",
                            )
                        ],
                    ),
                }
            ),
        )
        assert result_x.model_dump() == expected_result_x.model_dump()

        # Test flow_circular_y usage
        flow_y = Flow("flow_circular_y")
        result_y = flow_y.get_usage_info()

        # flow_circular_y should be used in flow_circular_x
        expected_result_y = UsageSearchResult(
            scope="Flow",
            name="flow_circular_y",
            usage=UsageData(
                flow={
                    "flow_circular_x": FlowFlowUsage(
                        direct=[DirectFlowUsageItem(flow_instance_name="container_to_y")],
                        indirect=[
                            IndirectFlowUsageItem(
                                flow_template_name="flow_circular_y",
                                flow_instance_name="container_to_y",
                            )
                        ],
                    ),
                    "flow_circular_y": FlowFlowUsage(
                        direct=[],
                        indirect=[
                            IndirectFlowUsageItem(
                                flow_template_name="flow_circular_x",
                                flow_instance_name="container_to_x",
                            )
                        ],
                    ),
                }
            ),
        )
        assert result_y.model_dump() == expected_result_y.model_dump()

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
            usage=UsageData(
                flow={
                    "flow_multi_a": NodeFlowUsage(
                        direct=[DirectNodeUsageItem(node_instance_name="test_node")],
                        indirect=[
                            IndirectNodeUsageItem(
                                flow_template_name="flow_multi_b",
                                flow_instance_name="container_to_b",
                            )
                        ],
                    ),
                    "flow_multi_b": NodeFlowUsage(
                        direct=[],
                        indirect=[
                            IndirectNodeUsageItem(
                                flow_template_name="flow_multi_c",
                                flow_instance_name="container_to_c",
                            )
                        ],
                    ),
                    "flow_multi_c": NodeFlowUsage(
                        direct=[],
                        indirect=[
                            IndirectNodeUsageItem(
                                flow_template_name="flow_multi_a",
                                flow_instance_name="container_to_a",
                            )
                        ],
                    ),
                }
            ),
        )
        assert result.model_dump() == expected_result.model_dump()


class TestCallbackUsageInfo:
    """Test suite for Callback.get_usage_info() method."""

    def test_callback_get_usage_info_direct_only(self, setup_test_data):
        """
        Test Callback.get_usage_info() with recursive=False (direct usages only).

        Test scenario:
        - place_holder callback is used in NodeSub1, NodeSub2, and UnusedNode
        - NodeSub1 and NodeSub2 are used in flows, but with recursive=False, we only want direct usages
        - UnusedNode is not used in any flow, but still uses the callback directly
        - Each node uses it in specific ports
        - With recursive=False, should only show direct node/port usage
        """

        callback = get_scope_instance("callback", "place_holder")
        result: UsageSearchResult = callback.get_usage_info(recursive=False)

        expected_result = UsageSearchResult(
            scope="Callback",
            name="place_holder",
            usage=UsageData(
                node={
                    "NodeSub1": CallbackNodeUsage(
                        direct=[DirectCallbackUsageItem(io_name="subport", iport_name="in")],
                        indirect=[],
                    ),
                    "NodeSub2": CallbackNodeUsage(
                        direct=[DirectCallbackUsageItem(io_name="subport", iport_name="in")],
                        indirect=[],
                    ),
                    "UnusedNode": CallbackNodeUsage(
                        direct=[DirectCallbackUsageItem(io_name="subport", iport_name="in")],
                        indirect=[],
                    ),
                }
            ),
        )
        assert result.model_dump() == expected_result.model_dump()

    def test_callback_get_usage_info_with_indirect(self, setup_test_data):
        """
        Test Callback.get_usage_info() with recursive=True (includes indirect usages via flows).

        Test scenario:
        - place_holder is used in NodeSub1 and NodeSub2
        - NodeSub1 appears in multiple flows with various instances
        - NodeSub2 appears in flow_with_four_nodes
        - UnusedNode is not used in any flow
        - Should show both direct (node/port) and indirect (flow/node_instance) usages
        """

        callback = get_scope_instance("callback", "place_holder")
        result: UsageSearchResult = callback.get_usage_info(recursive=True)

        expected_result = UsageSearchResult(
            scope="Callback",
            name="place_holder",
            usage=UsageData(
                node={
                    "NodeSub1": CallbackNodeUsage(
                        direct=[DirectCallbackUsageItem(io_name="subport", iport_name="in")],
                        indirect=[
                            IndirectCallbackUsageItem(
                                flow_name="flow_not_used_as_subflow", node_instance_name="sub"
                            ),
                            IndirectCallbackUsageItem(
                                flow_name="flow_with_duplicated_subflow", node_instance_name="sub1"
                            ),
                            IndirectCallbackUsageItem(
                                flow_name="flow_with_duplicated_subflow", node_instance_name="sub2"
                            ),
                            IndirectCallbackUsageItem(
                                flow_name="flow_with_four_nodes", node_instance_name="nodesub1"
                            ),
                            IndirectCallbackUsageItem(
                                flow_name="flow_with_nodes_and_subflow", node_instance_name="sub"
                            ),
                        ],
                    ),
                    "NodeSub2": CallbackNodeUsage(
                        direct=[DirectCallbackUsageItem(io_name="subport", iport_name="in")],
                        indirect=[
                            IndirectCallbackUsageItem(
                                flow_name="flow_with_four_nodes", node_instance_name="nodesub2"
                            ),
                        ],
                    ),
                    "UnusedNode": CallbackNodeUsage(
                        direct=[DirectCallbackUsageItem(io_name="subport", iport_name="in")],
                        indirect=[],
                    ),
                }
            ),
        )
        assert result.model_dump() == expected_result.model_dump()

    def test_unused_callback_get_usage_info(self, setup_test_data):
        """Test Callback.get_usage_info() for a callback that is not used in any node."""

        callback = get_scope_instance("callback", "unused_callback")
        result: UsageSearchResult = callback.get_usage_info(recursive=True)

        expected_result = UsageSearchResult(
            scope="Callback", name="unused_callback", usage=UsageData(node={})
        )
        assert result.model_dump() == expected_result.model_dump()

    def test_callback_get_usage_info_multiple_calls(self, setup_test_data):
        """
        Test that Callback.get_usage_info() can be called multiple times independently.

        Test scenario:
        - place_holder is used in 3 nodes (NodeSub1, NodeSub2, UnusedNode)
        - NodeSub1 has 5 flow instances, NodeSub2 has 1, UnusedNode has 0
        - unused_callback is not used anywhere
        """

        # Call multiple times for different callbacks
        callback1 = get_scope_instance("callback", "place_holder")
        callback2 = get_scope_instance("callback", "unused_callback")

        result1 = callback1.get_usage_info(recursive=True)
        result2 = callback2.get_usage_info(recursive=False)

        # Count total usages
        def count_usages(result):
            total_direct = 0
            total_indirect = 0
            if result.usage.node:
                for node_usage in result.usage.node.values():
                    total_direct += len(node_usage.direct)
                    total_indirect += len(node_usage.indirect)
            return total_direct, total_indirect

        direct1, indirect1 = count_usages(result1)
        direct2, indirect2 = count_usages(result2)

        # place_holder: 3 direct usages (3 nodes with callback)
        #               6 indirect usages (5 from NodeSub1 + 1 from NodeSub2)
        # unused_callback: 0 direct, 0 indirect
        assert direct1 == 3
        assert indirect1 == 6
        assert direct2 == 0
        assert indirect2 == 0

    def test_callback_parameter_validation(self, setup_test_data):
        """Test that recursive parameter properly controls indirect usage retrieval."""

        callback = get_scope_instance("callback", "place_holder")

        # With recursive=False, should have no indirect usages
        result_no_indirect = callback.get_usage_info(recursive=False)
        for node_name, node_usage in result_no_indirect.usage.node.items():
            assert (
                len(node_usage.indirect) == 0
            ), f"Node {node_name} should have no indirect usages with recursive=False"

        # With recursive=True, should have indirect usages for nodes used in flows
        result_with_indirect = callback.get_usage_info(recursive=True)

        # NodeSub1 and NodeSub2 are in flows, so should have indirect usages
        assert len(result_with_indirect.usage.node["NodeSub1"].indirect) > 0
        assert len(result_with_indirect.usage.node["NodeSub2"].indirect) > 0

        # UnusedNode is not in any flow, so should have no indirect usages
        assert len(result_with_indirect.usage.node["UnusedNode"].indirect) == 0
