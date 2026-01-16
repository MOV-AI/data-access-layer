"""Tests for mobdata search commands."""
import sys
from unittest.mock import patch


class TestMobdataSearchCommands:
    """Test suite for mobdata search commands using direct command invocation."""

    def _run_mobdata_search(self, obj_type, obj_name):
        """Helper to run mobdata search command programmatically using main()."""
        from dal.tools.mobdata import main

        # Build command line arguments
        cmd_args = ["mobdata", "usage-search", obj_type.lower(), obj_name]

        # Mock sys.argv to simulate command-line invocation
        with patch.object(sys, "argv", cmd_args):
            return_code = main()

        return return_code

    def test_search_node_command_nonexistent(self, global_db, setup_test_data, capsys):
        """Test mobdata search command for a node that doesn't exist."""
        # Run: mobdata usage-search node NonExistentNode
        return_code = self._run_mobdata_search("Node", "NonExistentNode")

        assert return_code == 1

        captured = capsys.readouterr()
        assert "Node 'NonExistentNode' does not exist." in captured.out

    def test_search_flow_command_not_used_as_subflow(self, global_db, setup_test_data, capsys):
        """Test mobdata search command for a flow that is not used as a subflow."""
        # Run: mobdata usage-search flow flow_not_used_as_subflow
        return_code = self._run_mobdata_search("Flow", "flow_not_used_as_subflow")

        assert return_code == 0

        captured = capsys.readouterr()
        assert "'flow_not_used_as_subflow' is not used anywhere" in captured.out

    def test_search_flow_command_nonexistent(self, global_db, setup_test_data, capsys):
        """Test mobdata search command for a flow that doesn't exist."""
        # Run: mobdata usage-search flow NonExistentFlow
        return_code = self._run_mobdata_search("Flow", "NonExistentFlow")

        assert return_code == 1

        captured = capsys.readouterr()
        assert "Flow 'NonExistentFlow' does not exist." in captured.out

    def test_search_node_command(self, global_db, setup_test_data, capsys):
        """Test mobdata search command for node usage."""
        # Run: mobdata usage-search node NodeSub1
        return_code = self._run_mobdata_search("Node", "NodeSub1")

        assert return_code == 0

        captured = capsys.readouterr()

        # Count: 4 direct instances + 3 indirect references = 7 total
        assert "NodeSub1" in captured.out
        assert (
            "'NodeSub1' is used in 8 location(s)" in captured.out.lower()
            or "nodesub1' is used in 8" in captured.out.lower()
        )

        # Check for direct usages (4 instances across 4 flows)
        assert "[direct] flow: flow_with_four_nodes" in captured.out.lower()
        assert "node instance: nodesub1" in captured.out.lower()

        assert "[direct] flow: flow_not_used_as_subflow" in captured.out.lower()
        assert "node instance: sub" in captured.out.lower()

        assert "[direct] flow: flow_with_duplicated_subflow" in captured.out.lower()
        assert "node instance: sub1" in captured.out.lower()
        assert "node instance: sub2" in captured.out.lower()

        assert "[direct] flow: flow_with_nodes_and_subflow" in captured.out.lower()
        assert "node instance: sub" in captured.out.lower()

        # Check for indirect usages (3 indirect references)
        assert "[indirect] flow: flow_with_duplicated_subflow" in captured.out.lower()
        assert "as sub flow: flow_with_four_nodes (instance: subflow1)" in captured.out.lower()
        assert "as sub flow: flow_with_four_nodes (instance: subflow2)" in captured.out.lower()

        assert "[indirect] flow: flow_with_nodes_and_subflow" in captured.out.lower()
        assert (
            "as sub flow: flow_with_duplicated_subflow (instance: subflow)" in captured.out.lower()
        )

    def test_search_flow_command(self, global_db, setup_test_data, capsys):
        """Test mobdata search command for flow usage as subflow."""
        # Run: mobdata usage-search flow flow_with_four_nodes
        return_code = self._run_mobdata_search("Flow", "flow_with_four_nodes")

        assert return_code == 0

        captured = capsys.readouterr()

        # Count: 2 direct instances + 1 indirect reference = 3 total
        assert "'flow_with_four_nodes' is used in 3 location(s)" in captured.out.lower()

        # Should show direct usage in flow_with_duplicated_subflow as subflow1 and subflow2
        assert "[direct] flow: flow_with_duplicated_subflow" in captured.out.lower()
        assert "flow instance (container): subflow1" in captured.out.lower()
        assert "flow instance (container): subflow2" in captured.out.lower()

        # Should show indirect usage in flow_with_nodes_and_subflow via flow_with_duplicated_subflow
        assert "[indirect] flow: flow_with_nodes_and_subflow" in captured.out.lower()
        assert (
            "as sub flow: flow_with_duplicated_subflow (instance: subflow)" in captured.out.lower()
        )
