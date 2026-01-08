"""Tests for mobdata search commands."""
import pytest
import sys
from unittest.mock import patch


class TestMobdataSearchCommands:
    """Test suite for mobdata search commands using direct command invocation."""

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
                print(f"Failed to remove node {node_name} during cleanup.")

        for flow_name in ["flow_1", "flow_2", "flow_3", "flow_4"]:
            try:
                flow = Flow(flow_name)
                flow.remove(force=True)
            except Exception:
                print(f"Failed to remove flow {flow_name} during cleanup.")

    def _run_mobdata_search(self, obj_type, obj_name, recursive=False):
        """Helper to run mobdata search command programmatically using main()."""
        from dal.tools.mobdata import main

        # Build command line arguments
        cmd_args = ["mobdata", "usage-search", obj_type.lower(), obj_name]
        if not recursive:
            cmd_args.append("--individual")

        # Mock sys.argv to simulate command-line invocation
        with patch.object(sys, "argv", cmd_args):
            return_code = main()

        return return_code

    def test_search_node_command_direct_usage(self, global_db, capsys):
        """Test mobdata search command for node usage without recursion."""
        # Run: mobdata usage-search node NodeSub1
        return_code = self._run_mobdata_search("Node", "NodeSub1", recursive=False)

        # Command should succeed
        assert return_code == 0

        # Check output
        captured = capsys.readouterr()
        assert "'NodeSub1' is used in 5 flow(s)" in captured.out
        assert "[direct] flow: flow_1, nodeinst: nodesub1" in captured.out.lower()
        assert "[direct] flow: flow_2, nodeinst: sub" in captured.out.lower()
        assert "[direct] flow: flow_3, nodeinst: sub1" in captured.out.lower()
        assert "[direct] flow: flow_3, nodeinst: sub2" in captured.out.lower()
        assert "[direct] flow: flow_4, nodeinst: sub" in captured.out.lower()

    def test_search_node_command_single_usage(self, global_db, capsys):
        """Test mobdata search command for a node used in only one flow."""
        # Run: mobdata usage-search node NodeSub2
        return_code = self._run_mobdata_search("Node", "NodeSub2", recursive=False)

        assert return_code == 0

        captured = capsys.readouterr()
        assert "'NodeSub2' is used in 1 flow(s)" in captured.out
        assert "[direct] flow: flow_1, nodeinst: nodesub2" in captured.out.lower()

    def test_search_node_command_nonexistent(self, global_db, capsys):
        """Test mobdata search command for a node that doesn't exist."""
        # Run: mobdata usage-search node NonExistentNode
        return_code = self._run_mobdata_search("Node", "NonExistentNode", recursive=False)

        # Should still return 0 (not a fatal error)
        assert return_code == 0

        captured = capsys.readouterr()
        assert "Error" in captured.err or "does not exist" in captured.err

    def test_search_flow_command_as_subflow_direct(self, global_db, capsys):
        """Test mobdata search command for flow usage as subflow without recursion."""
        # Run: mobdata usage-search flow flow_1
        return_code = self._run_mobdata_search("Flow", "flow_1", recursive=False)

        assert return_code == 0

        captured = capsys.readouterr()
        assert "'flow_1' is used in 2 flow(s)" in captured.out
        assert "[direct] flow: flow_3, container: subflow1" in captured.out.lower()
        assert "[direct] flow: flow_3, container: subflow2" in captured.out.lower()

    def test_search_flow_command_not_used_as_subflow(self, global_db, capsys):
        """Test mobdata search command for a flow that is not used as a subflow."""
        # Run: mobdata usage-search flow flow_2
        return_code = self._run_mobdata_search("Flow", "flow_2", recursive=False)

        assert return_code == 0

        captured = capsys.readouterr()
        assert "'flow_2' is not used in any flows" in captured.out

    def test_search_flow_command_nonexistent(self, global_db, capsys):
        """Test mobdata search command for a flow that doesn't exist."""
        # Run: mobdata usage-search flow NonExistentFlow
        return_code = self._run_mobdata_search("Flow", "NonExistentFlow", recursive=False)

        assert return_code == 0

        captured = capsys.readouterr()
        assert "Error" in captured.err or "does not exist" in captured.err

    def test_search_node_command_recursive(self, global_db, capsys):
        """Test mobdata search command for node usage with recursion."""
        # Run: mobdata usage-search node NodeSub1
        return_code = self._run_mobdata_search("Node", "NodeSub1", recursive=True)

        assert return_code == 0

        captured = capsys.readouterr()
        assert "NodeSub1" in captured.out
        assert "'nodesub1' is used in 9 flow(s)" in captured.out.lower()
        # Should have both direct and indirect usages in output
        assert "[direct] flow: flow_1, nodeinst: nodesub1" in captured.out.lower()
        assert "[direct] flow: flow_2, nodeinst: sub" in captured.out.lower()
        assert "[direct] flow: flow_3, nodeinst: sub1" in captured.out.lower()
        assert "[direct] flow: flow_3, nodeinst: sub2" in captured.out.lower()
        assert "[direct] flow: flow_4, nodeinst: sub" in captured.out.lower()
        assert "[indirect] flow: flow_3, nodeinst: nodesub1" in captured.out.lower()
        assert (
            "path: {'flow': 'flow_3', 'container': 'subflow1'} -> {'flow': 'flow_1', 'nodeinst': 'nodesub1'}"
            in captured.out.lower()
        )
        assert "[indirect] flow: flow_4, nodeinst: nodesub1" in captured.out.lower()
        assert (
            "path: {'flow': 'flow_4', 'container': 'subflow3'} -> {'flow': 'flow_3', 'container': 'subflow1'} -> {'flow': 'flow_1', 'nodeinst': 'nodesub1'}"
            in captured.out.lower()
        )
        assert "[indirect] flow: flow_4, nodeinst: sub1" in captured.out.lower()
        assert (
            "path: {'flow': 'flow_4', 'container': 'subflow3'} -> {'flow': 'flow_3', 'nodeinst': 'sub1'}"
            in captured.out.lower()
        )
        assert "[indirect] flow: flow_4, nodeinst: sub2" in captured.out.lower()
        assert (
            "path: {'flow': 'flow_4', 'container': 'subflow3'} -> {'flow': 'flow_3', 'nodeinst': 'sub2'}"
            in captured.out.lower()
        )

    def test_search_flow_command_recursive(self, global_db, capsys):
        """Test mobdata search command for flow usage as subflow with recursion."""
        # Run: mobdata usage-search flow flow_1
        return_code = self._run_mobdata_search("Flow", "flow_1", recursive=True)

        assert return_code == 0

        captured = capsys.readouterr()
        assert "'flow_1' is used in 4 flow(s)" in captured.out.lower()
        # Should show direct usage in flow_3 as subflow1 and subflow2
        assert "[direct] flow: flow_3, container: subflow1" in captured.out.lower()
        assert "[direct] flow: flow_3, container: subflow2" in captured.out.lower()
        # Should also show indirect usage in flow_4 via flow_3
        assert "[indirect] flow: flow_4, container: subflow3" in captured.out.lower()
        assert (
            "path: {'flow': 'flow_4', 'container': 'subflow3'} -> {'flow': 'flow_3', 'container': 'subflow1'}"
            in captured.out.lower()
        )
        assert (
            "path: {'flow': 'flow_4', 'container': 'subflow3'} -> {'flow': 'flow_3', 'container': 'subflow2'}"
            in captured.out.lower()
        )
