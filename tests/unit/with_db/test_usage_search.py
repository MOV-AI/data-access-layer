"""Tests for usage search functionality in DAL."""
import pytest


class TestUsageSearch:
    """Test suite for node and flow usage search methods."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, global_db, metadata_folder):
        """Import test metadata before each test."""
        from dal.tools.backup import Importer

        # Import all nodes and flows for testing
        importer = Importer(
            metadata_folder,
            force=True,
            dry=False,
            debug=True,  # Enable debug to see what's happening
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

    def test_search_node_direct_usage(self, global_db):
        """
        Test searching for node usage without recursion.

        Test scenario (based on metadata):
        - NodeSub1 is used in flow_1 (as 'nodesub1'), flow_2 (as 'sub'), flow_3 (as 'sub'), flow_4 (as 'sub')
        - NodeSub2 is used in flow_1 (as 'nodesub2')
        - NodePub1 is used in flow_1 (as 'nodepub1'), flow_2 (as 'pub'), flow_3 (as 'pub'), flow_4 (as 'pub')

        Expected result for NodeSub1:
        {
            'node': 'NodeSub1',
            'usage': [
                {'flow': 'flow_1', 'NodeInst': 'nodesub1', 'direct': True},
                {'flow': 'flow_2', 'NodeInst': 'sub', 'direct': True},
                {'flow': 'flow_3', 'NodeInst': 'sub', 'direct': True},
                {'flow': 'flow_4', 'NodeInst': 'sub', 'direct': True}
            ]
        }
        """
        from dal.tools.backup import Searcher

        searcher = Searcher(debug=False)

        # Test NodeSub1 usage
        result = searcher.search_node("NodeSub1", recursive=False)

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

    def test_search_node_single_usage(self, global_db):
        """Test searching for a node used in only one flow."""
        from dal.tools.backup import Searcher

        searcher = Searcher(debug=False)

        # Test NodeSub2 usage (only in flow_1)
        result = searcher.search_node("NodeSub2", recursive=False)

        assert result["node"] == "NodeSub2"
        assert "usage" in result
        assert "error" not in result
        assert len(result["usage"]) == 1

        usage = result["usage"][0]
        assert usage["flow"] == "flow_1"
        assert usage["NodeInst"] == "nodesub2"
        assert usage["direct"] is True

    def test_search_node_nonexistent(self, global_db):
        """Test searching for a node that doesn't exist."""
        from dal.tools.backup import Searcher

        searcher = Searcher(debug=False)

        result = searcher.search_node("NonExistentNode", recursive=False)

        assert result["node"] == "NonExistentNode"
        assert "error" in result
        assert "does not exist" in result["error"]
        assert "usage" in result

    def test_search_flow_as_subflow_direct(self, global_db):
        """
        Test searching for flow usage as subflow without recursion.

        Test scenario (based on metadata):
        - flow_1 is used as a subflow in flow_3 (Container: 'subflow1')
        - flow_3 is used as a subflow in flow_4 (Container: 'subflow3')
        - flow_2 is not used as a subflow anywhere

        Expected result for flow_1:
        {
            'flow': 'flow_1',
            'usage': [
                {'flow': 'flow_3', 'Container': 'subflow1', 'direct': True}
            ]
        }
        """
        from dal.tools.backup import Searcher

        searcher = Searcher(debug=False)

        # Test flow_1 usage as subflow
        result = searcher.search_flow("flow_1", recursive=False)

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

    def test_search_flow_not_used_as_subflow(self, global_db):
        """Test searching for a flow that is not used as a subflow."""
        from dal.tools.backup import Searcher

        searcher = Searcher(debug=False)

        # Test flow_2 usage (not used as subflow anywhere)
        result = searcher.search_flow("flow_2", recursive=False)

        assert result["flow"] == "flow_2"
        assert "usage" in result
        assert "error" not in result
        assert len(result["usage"]) == 0

    def test_search_flow_nonexistent(self, global_db):
        """Test searching for a flow that doesn't exist."""
        from dal.tools.backup import Searcher

        searcher = Searcher(debug=False)

        result = searcher.search_flow("NonExistentFlow", recursive=False)

        assert result["flow"] == "NonExistentFlow"
        assert "error" in result
        assert "does not exist" in result["error"]
        assert "usage" in result

    def test_search_node_recursive(self, global_db):
        """
        Test searching for node usage with recursion.

        Test scenario:
        - NodeSub1 is directly in flow_1, flow_2, flow_3, flow_4
        - flow_1 is a subflow in flow_3
        - flow_3 is a subflow in flow_4
        - Therefore NodeSub1 should appear:
          - Directly in flow_1, flow_2, flow_3, flow_4
          - Indirectly in flow_3 (via flow_1 which contains nodesub1)
          - Indirectly in flow_4 (via flow_3 -> flow_1)
        """
        from dal.tools.backup import Searcher

        searcher = Searcher(debug=False)

        result = searcher.search_node("NodeSub1", recursive=True)

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

        # Indirect usages should exist (at least flow_3 via flow_1)
        assert len(indirect_usages) >= 1

        # Verify at least one indirect usage has a path
        indirect_with_path = [item for item in indirect_usages if "path" in item]
        assert len(indirect_with_path) >= 1

    def test_search_flow_recursive(self, global_db):
        """
        Test searching for flow usage as subflow with recursion.

        Test scenario:
        - flow_1 is directly used in flow_3
        - flow_3 is directly used in flow_4
        - Therefore flow_1 should appear:
          - Directly in flow_3
          - Indirectly in flow_4 (via flow_3)
        """
        from dal.tools.backup import Searcher

        searcher = Searcher(debug=False)

        result = searcher.search_flow("flow_1", recursive=True)

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

    def test_print_results_node(self, global_db, capsys):
        """Test the print_results method for node search."""
        from dal.tools.backup import Searcher

        searcher = Searcher(debug=False)

        result = searcher.search_node("NodeSub2", recursive=False)
        searcher.print_results(result, "node")

        captured = capsys.readouterr()
        assert "NodeSub2" in captured.out
        assert "flow_1" in captured.out
        assert "nodesub2" in captured.out

    def test_print_results_flow(self, global_db, capsys):
        """Test the print_results method for flow search."""
        from dal.tools.backup import Searcher

        searcher = Searcher(debug=False)

        result = searcher.search_flow("flow_1", recursive=False)
        searcher.print_results(result, "flow")

        captured = capsys.readouterr()
        assert "flow_1" in captured.out
        assert "flow_3" in captured.out
        assert "subflow1" in captured.out

    def test_print_results_not_found(self, global_db, capsys):
        """Test the print_results method for non-existent items."""
        from dal.tools.backup import Searcher

        searcher = Searcher(debug=False)

        result = searcher.search_node("NonExistent", recursive=False)
        searcher.print_results(result, "node")

        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "does not exist" in captured.err

    def test_print_results_not_used(self, global_db, capsys):
        """Test the print_results method for items not used anywhere."""
        from dal.tools.backup import Searcher

        searcher = Searcher(debug=False)

        result = searcher.search_flow("flow_2", recursive=False)
        searcher.print_results(result, "flow")

        captured = capsys.readouterr()
        assert "flow_2" in captured.out
        assert "not used in any flows" in captured.out
