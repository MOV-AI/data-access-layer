"""Tests for Node and Flow classmethod usage search functionality."""
import pytest

from movai_core_shared.exceptions import DoesNotExist

from dal.scopes.flow import Flow
from dal.scopes.node import Node


SCOPE_MAP = {
    "node": Node,
    "flow": Flow,
}


def get_scope_instance(search_type, name):
    """Helper to get scope instance based on type and name."""
    try:
        scope = SCOPE_MAP[search_type](name)
    except DoesNotExist as e:
        raise e
    return scope


class TestNodeUsageInfo:
    """Test suite for Node.get_usage_info() classmethod."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, global_db, metadata_folder):
        """Import test metadata before each test."""
        from dal.tools.backup import Importer

        # Import all nodes and flows for testing
        importer = Importer(
            metadata_folder,
            force=True,
            dry=False,
            debug=False,
            recursive=True,
            clean_old_data=True,
        )

        # Import nodes first, then flows (flows depend on nodes)
        objects = {
            "Node": ["NodePub1", "NodePub2", "NodeSub1", "NodeSub2"],
        }
        importer.run(objects)

        # Now import flows
        objects = {
            "Flow": ["flow_1", "flow_2", "flow_3", "flow_4"],
        }
        importer.run(objects)

        yield

        # Cleanup after test
        for node_name in ["NodePub1", "NodePub2", "NodeSub1", "NodeSub2"]:
            try:
                node = Node(node_name)
                node.remove(force=True)
            except Exception:
                print(f"Failed to remove node {node_name} during cleanup.")

        for flow_name in ["flow_1", "flow_2", "flow_3", "flow_4"]:
            try:
                flow = Flow(flow_name)
                flow.remove(force=True)
            except Exception:
                print(f"Failed to remove flow {flow_name} during cleanup.")

    def test_node_get_usage_info(self, global_db):
        """
        Test Node.get_usage_info() with recursive search.

        Test scenario:
        - NodeSub1 is directly in flow_1, flow_2, flow_3, flow_4
        - flow_1 is a subflow in flow_3
        - flow_3 is a subflow in flow_4
        - Therefore NodeSub1 should appear with both direct and indirect usages
        """

        node = get_scope_instance("node", "NodeSub1")
        usage = node.get_usage_info()

        # Should have both direct and indirect usages
        direct_usages = [item for item in usage if item.get("direct", True)]
        indirect_usages = [item for item in usage if not item.get("direct", True)]
        # Direct usages: flow_1, flow_2, flow_3, flow_4
        assert len(direct_usages) == 5
        direct_flows = {item["flow"] for item in direct_usages}
        assert direct_flows == {"flow_1", "flow_2", "flow_3", "flow_4"}

        # Indirect usages should exist
        assert len(indirect_usages) >= 1

        # Verify at least one indirect usage has a path
        indirect_with_path = [item for item in indirect_usages if "path" in item]
        assert len(indirect_with_path) >= 1

    def test_node_get_usage_info_multiple_calls(self, global_db):
        """Test that Node.get_usage_info() can be called multiple times without instantiation."""

        # Call multiple times for different nodes
        node1 = get_scope_instance("node", "NodeSub1")
        node2 = get_scope_instance("node", "NodeSub2")
        node3 = get_scope_instance("node", "NodePub1")

        usage1 = node1.get_usage_info()
        usage2 = node2.get_usage_info()
        usage3 = node3.get_usage_info()

        # Each should have independent results
        assert len(usage1) == 9
        assert len(usage2) == 3
        assert len(usage3) == 7


class TestFlowUsageInfo:
    """Test suite for Flow.get_usage_info() classmethod."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, global_db, metadata_folder):
        """Import test metadata before each test."""
        from dal.tools.backup import Importer

        # Import all nodes and flows for testing
        importer = Importer(
            metadata_folder,
            force=True,
            dry=False,
            debug=False,
            recursive=True,
            clean_old_data=True,
        )

        # Import nodes first, then flows (flows depend on nodes)
        objects = {
            "Node": ["NodePub1", "NodePub2", "NodeSub1", "NodeSub2"],
        }
        importer.run(objects)

        # Now import flows
        objects = {
            "Flow": ["flow_1", "flow_2", "flow_3", "flow_4"],
        }
        importer.run(objects)

        yield

        # Cleanup after test
        for node_name in ["NodePub1", "NodePub2", "NodeSub1", "NodeSub2"]:
            try:
                node = Node(node_name)
                node.remove(force=True)
            except Exception:
                print(f"Failed to remove node {node_name} during cleanup.")

        for flow_name in ["flow_1", "flow_2", "flow_3", "flow_4"]:
            try:
                flow = Flow(flow_name)
                flow.remove(force=True)
            except Exception:
                print(f"Failed to remove flow {flow_name} during cleanup.")

    def test_flow_get_usage_info_not_used_as_subflow(self, global_db):
        """Test Flow.get_usage_info() for a flow that is not used as a subflow."""

        # Test flow_2 usage (not used as subflow anywhere)
        flow = get_scope_instance("flow", "flow_2")
        usage = flow.get_usage_info()

        assert len(usage) == 0

    def test_flow_get_usage_info(self, global_db):
        """
        Test Flow.get_usage_info() with recursive search.

        Test scenario:
        - flow_1 is directly used in flow_3
        - flow_3 is directly used in flow_4
        - Therefore flow_1 should appear:
          - Directly in flow_3
          - Indirectly in flow_4 (via flow_3)
        """

        flow = get_scope_instance("flow", "flow_1")
        usage = flow.get_usage_info()

        # Should have both direct and indirect usages
        direct_usages = [item for item in usage if item.get("direct", True)]
        indirect_usages = [item for item in usage if not item.get("direct", True)]

        # Direct usage: flow_3 (twice as subflow1 and subflow2)
        assert len(direct_usages) == 2
        assert {"flow": "flow_3", "Container": "subflow1", "direct": True} in direct_usages
        assert {"flow": "flow_3", "Container": "subflow2", "direct": True} in direct_usages

        # Indirect usages should exist (flow_4 via flow_3)
        assert len(indirect_usages) >= 1

        # Verify indirect usages have paths
        for item in indirect_usages:
            assert "path" in item
            assert isinstance(item["path"], list)
            assert len(item["path"]) >= 2  # At least 2 hops in the path

    def test_flow_get_usage_info_nested_subflow(self, global_db):
        """Test Flow.get_usage_info() for flow_3 which is used in flow_4."""

        flow = get_scope_instance("flow", "flow_3")
        usage = flow.get_usage_info()

        assert len(usage) == 1

        usage = usage[0]
        assert usage["flow"] == "flow_4"
        assert usage["Container"] == "subflow3"
        assert usage["direct"] is True

    def test_flow_get_usage_info_multiple_calls(self, global_db):
        """Test that Flow.get_usage_info() can be called multiple times without instantiation."""

        # Call multiple times for different flows
        flow1 = get_scope_instance("flow", "flow_1")
        flow2 = get_scope_instance("flow", "flow_2")
        flow3 = get_scope_instance("flow", "flow_3")

        usage1 = flow1.get_usage_info()
        usage2 = flow2.get_usage_info()
        usage3 = flow3.get_usage_info()

        print(len(usage1), len(usage2), len(usage3))

        # Each should have independent results
        assert len(usage1) == 4
        assert len(usage2) == 0
        assert len(usage3) == 1
