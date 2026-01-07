"""Tests for Node and Flow classmethod usage search functionality."""
import pytest


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
        from dal.scopes.node import Node
        from dal.scopes.flow import Flow

        # Delete all test data
        for node_name in ["NodePub1", "NodePub2", "NodeSub1", "NodeSub2"]:
            try:
                node = Node(node_name)
                node.remove(force=True)
            except Exception:
                pass

        for flow_name in ["flow_1", "flow_2", "flow_3", "flow_4"]:
            try:
                flow = Flow(flow_name)
                flow.remove(force=True)
            except Exception:
                pass

    def test_node_get_usage_info_direct(self, global_db):
        """
        Test Node.get_usage_info() classmethod for direct usage.

        Test scenario (based on metadata):
        - NodeSub1 is used in flow_1 (as 'nodesub1'), flow_2 (as 'sub'), flow_3 (as 'sub'), flow_4 (as 'sub')
        """
        from dal.scopes.node import Node

        # Test using classmethod directly
        result = Node.get_usage_info("NodeSub1", recursive=False)

        assert result["node"] == "NodeSub1"
        assert "usage" in result
        assert "error" not in result
        assert isinstance(result["usage"], list)

        # NodeSub1 should be used in 4 flows directly
        assert len(result["usage"]) == 4

        # Check all flows are present
        flow_names = {item["flow"] for item in result["usage"]}
        assert flow_names == {"flow_1", "flow_2", "flow_3", "flow_4"}

        # Verify all are marked as direct
        assert all(item["direct"] for item in result["usage"])

        # Verify specific NodeInst names
        usage_map = {item["flow"]: item["NodeInst"] for item in result["usage"]}
        assert usage_map["flow_1"] == "nodesub1"
        assert usage_map["flow_2"] == "sub"
        assert usage_map["flow_3"] == "sub"
        assert usage_map["flow_4"] == "sub"

    def test_node_get_usage_info_single_usage(self, global_db):
        """Test Node.get_usage_info() for a node used in only one flow."""
        from dal.scopes.node import Node

        # Test NodeSub2 usage (only in flow_1)
        result = Node.get_usage_info("NodeSub2", recursive=False)

        assert result["node"] == "NodeSub2"
        assert "usage" in result
        assert "error" not in result
        assert len(result["usage"]) == 1

        usage = result["usage"][0]
        assert usage["flow"] == "flow_1"
        assert usage["NodeInst"] == "nodesub2"
        assert usage["direct"] is True

    def test_node_get_usage_info_nonexistent(self, global_db):
        """Test Node.get_usage_info() for a node that doesn't exist."""
        from dal.scopes.node import Node

        result = Node.get_usage_info("NonExistentNode", recursive=False)

        assert result["node"] == "NonExistentNode"
        assert "error" in result
        assert "does not exist" in result["error"]
        assert "usage" in result
        assert len(result["usage"]) == 0

    def test_node_get_usage_info_recursive(self, global_db):
        """
        Test Node.get_usage_info() with recursive search.

        Test scenario:
        - NodeSub1 is directly in flow_1, flow_2, flow_3, flow_4
        - flow_1 is a subflow in flow_3
        - flow_3 is a subflow in flow_4
        - Therefore NodeSub1 should appear with both direct and indirect usages
        """
        from dal.scopes.node import Node

        result = Node.get_usage_info("NodeSub1", recursive=True)

        assert result["node"] == "NodeSub1"
        assert "usage" in result
        assert "error" not in result

        # Should have both direct and indirect usages
        direct_usages = [item for item in result["usage"] if item.get("direct", True)]
        indirect_usages = [item for item in result["usage"] if not item.get("direct", True)]

        # Direct usages: flow_1, flow_2, flow_3, flow_4
        assert len(direct_usages) == 4
        direct_flows = {item["flow"] for item in direct_usages}
        assert direct_flows == {"flow_1", "flow_2", "flow_3", "flow_4"}

        # Indirect usages should exist
        assert len(indirect_usages) >= 1

        # Verify at least one indirect usage has a path
        indirect_with_path = [item for item in indirect_usages if "path" in item]
        assert len(indirect_with_path) >= 1

    def test_node_get_usage_info_multiple_calls(self, global_db):
        """Test that Node.get_usage_info() can be called multiple times without instantiation."""
        from dal.scopes.node import Node

        # Call multiple times for different nodes
        result1 = Node.get_usage_info("NodeSub1", recursive=False)
        result2 = Node.get_usage_info("NodeSub2", recursive=False)
        result3 = Node.get_usage_info("NodePub1", recursive=False)

        assert result1["node"] == "NodeSub1"
        assert result2["node"] == "NodeSub2"
        assert result3["node"] == "NodePub1"

        # Each should have independent results
        assert len(result1["usage"]) == 4
        assert len(result2["usage"]) == 1
        assert len(result3["usage"]) == 4


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
        from dal.scopes.node import Node
        from dal.scopes.flow import Flow

        # Delete all test data
        for node_name in ["NodePub1", "NodePub2", "NodeSub1", "NodeSub2"]:
            try:
                node = Node(node_name)
                node.remove(force=True)
            except Exception:
                pass

        for flow_name in ["flow_1", "flow_2", "flow_3", "flow_4"]:
            try:
                flow = Flow(flow_name)
                flow.remove(force=True)
            except Exception:
                pass

    def test_flow_get_usage_info_as_subflow_direct(self, global_db):
        """
        Test Flow.get_usage_info() classmethod for direct usage as subflow.

        Test scenario (based on metadata):
        - flow_1 is used as a subflow in flow_3 (Container: 'subflow1')
        """
        from dal.scopes.flow import Flow

        # Test using classmethod directly
        result = Flow.get_usage_info("flow_1", recursive=False)

        assert result["flow"] == "flow_1"
        assert "usage" in result
        assert "error" not in result
        assert isinstance(result["usage"], list)

        # flow_1 is used directly in flow_3
        assert len(result["usage"]) == 1

        usage = result["usage"][0]
        assert usage["flow"] == "flow_3"
        assert usage["Container"] == "subflow1"
        assert usage["direct"] is True

    def test_flow_get_usage_info_not_used_as_subflow(self, global_db):
        """Test Flow.get_usage_info() for a flow that is not used as a subflow."""
        from dal.scopes.flow import Flow

        # Test flow_2 usage (not used as subflow anywhere)
        result = Flow.get_usage_info("flow_2", recursive=False)

        assert result["flow"] == "flow_2"
        assert "usage" in result
        assert "error" not in result
        assert len(result["usage"]) == 0

    def test_flow_get_usage_info_nonexistent(self, global_db):
        """Test Flow.get_usage_info() for a flow that doesn't exist."""
        from dal.scopes.flow import Flow

        result = Flow.get_usage_info("NonExistentFlow", recursive=False)

        assert result["flow"] == "NonExistentFlow"
        assert "error" in result
        assert "does not exist" in result["error"]
        assert "usage" in result
        assert len(result["usage"]) == 0

    def test_flow_get_usage_info_recursive(self, global_db):
        """
        Test Flow.get_usage_info() with recursive search.

        Test scenario:
        - flow_1 is directly used in flow_3
        - flow_3 is directly used in flow_4
        - Therefore flow_1 should appear:
          - Directly in flow_3
          - Indirectly in flow_4 (via flow_3)
        """
        from dal.scopes.flow import Flow

        result = Flow.get_usage_info("flow_1", recursive=True)

        assert result["flow"] == "flow_1"
        assert "usage" in result
        assert "error" not in result

        # Should have both direct and indirect usages
        direct_usages = [item for item in result["usage"] if item.get("direct", True)]
        indirect_usages = [item for item in result["usage"] if not item.get("direct", True)]

        # Direct usage: flow_3
        assert len(direct_usages) == 1
        assert direct_usages[0]["flow"] == "flow_3"
        assert direct_usages[0]["Container"] == "subflow1"

        # Indirect usages should exist (flow_4 via flow_3)
        assert len(indirect_usages) >= 1

        # Verify indirect usages have paths
        for item in indirect_usages:
            assert "path" in item
            assert isinstance(item["path"], list)
            assert len(item["path"]) >= 2  # At least 2 hops in the path

    def test_flow_get_usage_info_nested_subflow(self, global_db):
        """Test Flow.get_usage_info() for flow_3 which is used in flow_4."""
        from dal.scopes.flow import Flow

        result = Flow.get_usage_info("flow_3", recursive=False)

        assert result["flow"] == "flow_3"
        assert "usage" in result
        assert "error" not in result
        assert len(result["usage"]) == 1

        usage = result["usage"][0]
        assert usage["flow"] == "flow_4"
        assert usage["Container"] == "subflow3"
        assert usage["direct"] is True

    def test_flow_get_usage_info_multiple_calls(self, global_db):
        """Test that Flow.get_usage_info() can be called multiple times without instantiation."""
        from dal.scopes.flow import Flow

        # Call multiple times for different flows
        result1 = Flow.get_usage_info("flow_1", recursive=False)
        result2 = Flow.get_usage_info("flow_2", recursive=False)
        result3 = Flow.get_usage_info("flow_3", recursive=False)

        assert result1["flow"] == "flow_1"
        assert result2["flow"] == "flow_2"
        assert result3["flow"] == "flow_3"

        # Each should have independent results
        assert len(result1["usage"]) == 1
        assert len(result2["usage"]) == 0
        assert len(result3["usage"]) == 1
