import unittest
from unittest.mock import patch

from dal.scopes.node import Node
from movai_core_shared import (
    MOVAI_NODE,
    MOVAI_SERVER,
    MOVAI_STATE,
    MOVAI_TRANSITIONFOR,
    ROS1_NODE,
    ROS1_NODELET,
    ROS1_PLUGIN,
)


class TestNodeSetType(unittest.TestCase):
    def test_set_type_with_ros1_plugin(self):
        with patch("dal.scopes.node.MovaiDB") as MockMovaiDB:
            with patch("dal.scopes.scope.MovaiDB", new=MockMovaiDB):
                mock_db_instance = MockMovaiDB.return_value
                mock_db_instance.get.side_effect = [
                    {
                        "Node": {
                            "test_node": {"PortsInst": {"port1": {"Template": "ROS1/PluginClient"}}}
                        }
                    }
                ]
                mock_db_instance.get_value.side_effect = ["test_path"]

                node = Node("test_node")
                node.set_type()

                # Verify that set was called with ROS1_PLUGIN
                mock_db_instance.set.assert_called_once_with(
                    {"Node": {"test_node": {"Type": ROS1_PLUGIN}}}
                )

    def test_set_type_with_ros1_node(self):
        with patch("dal.scopes.node.MovaiDB") as MockMovaiDB:
            with patch("dal.scopes.scope.MovaiDB", new=MockMovaiDB):
                # Set up mock behavior for a case where it should set type to ROS1_NODE
                mock_db_instance = MockMovaiDB.return_value
                mock_db_instance.get.side_effect = [
                    {"Node": {"test_node": {"PortsInst": {"port1": {"Template": "SomeTemplate"}}}}}
                ]
                mock_db_instance.get_value.side_effect = ["test_path"]

                node = Node("test_node")
                node.set_type()

                # Verify that set was called with ROS1_NODE due to the updated else condition
                mock_db_instance.set.assert_called_once_with(
                    {"Node": {"test_node": {"Type": ROS1_NODE}}}
                )

    def test_set_type_with_ros1_nodelet(self):
        with patch("dal.scopes.node.MovaiDB") as MockMovaiDB:
            with patch("dal.scopes.scope.MovaiDB", new=MockMovaiDB):
                mock_db_instance = MockMovaiDB.return_value
                mock_db_instance.get.side_effect = [
                    {"Node": {"test_node": {"PortsInst": {"port1": {"Template": "ROS1/Nodelet"}}}}}
                ]
                mock_db_instance.get_value.side_effect = ["test_path"]

                node = Node("test_node")
                node.set_type()

                # Verify that set was called with ROS1_NODELET
                mock_db_instance.set.assert_called_once_with(
                    {"Node": {"test_node": {"Type": ROS1_NODELET}}}
                )

    def test_set_type_with_movai_server(self):
        with patch("dal.scopes.node.MovaiDB") as MockMovaiDB:
            with patch("dal.scopes.scope.MovaiDB", new=MockMovaiDB):
                # Set up mock behavior to test setting MOVAI_SERVER
                mock_db_instance = MockMovaiDB.return_value
                mock_db_instance.get.side_effect = [
                    {"Node": {"test_node": {"PortsInst": {"port1": {"Template": "Http"}}}}}
                ]
                mock_db_instance.get_value.side_effect = ["test_path"]

                node = Node("test_node")
                node.set_type()

                # Verify that set was called with MOVAI_SERVER
                mock_db_instance.set.assert_called_once_with(
                    {"Node": {"test_node": {"Type": MOVAI_SERVER}}}
                )

    def test_set_type_with_movai_state(self):
        with patch("dal.scopes.node.MovaiDB") as MockMovaiDB:
            with patch("dal.scopes.scope.MovaiDB", new=MockMovaiDB):
                # Set up mock behavior to test setting MOVAI_STATE
                mock_db_instance = MockMovaiDB.return_value
                mock_db_instance.get.side_effect = [
                    {
                        "Node": {
                            "test_node": {"PortsInst": {"port1": {"Template": MOVAI_TRANSITIONFOR}}}
                        }
                    }
                ]
                mock_db_instance.get_value.side_effect = ["test_path"]

                node = Node("test_node")
                node.set_type()

                # Verify that set was called with MOVAI_STATE
                mock_db_instance.set.assert_called_once_with(
                    {"Node": {"test_node": {"Type": MOVAI_STATE}}}
                )

    def test_set_type_default_movai_node(self):
        with patch("dal.scopes.node.MovaiDB") as MockMovaiDB:
            with patch("dal.scopes.scope.MovaiDB", new=MockMovaiDB):
                # Set up mock behavior where no ports and no path match specific templates
                mock_db_instance = MockMovaiDB.return_value
                mock_db_instance.get.side_effect = [
                    {"Node": {"test_node": {"PortsInst": {}}}}
                ]  # No ports
                mock_db_instance.get_value.side_effect = [None]  # No path

                node = Node("test_node")
                node.set_type()

                # Verify that set was called with MOVAI_NODE as the default type
                mock_db_instance.set.assert_called_once_with(
                    {"Node": {"test_node": {"Type": MOVAI_NODE}}}
                )

    def test_set_type_no_ports_with_path(self):
        with patch("dal.scopes.node.MovaiDB") as MockMovaiDB:
            with patch("dal.scopes.scope.MovaiDB", new=MockMovaiDB):
                # New test case: Empty "PortsInst" and non-empty "Path"
                mock_db_instance = MockMovaiDB.return_value
                mock_db_instance.get.side_effect = [
                    {"Node": {"test_node": {"PortsInst": {}}}}
                ]  # No ports
                mock_db_instance.get_value.side_effect = ["/test/path"]  # Path is set

                node = Node("test_node")
                node.set_type()

                # Verify that set was called with ROS1_NODE since path is set
                mock_db_instance.set.assert_called_once_with(
                    {"Node": {"test_node": {"Type": ROS1_NODE}}}
                )


if __name__ == "__main__":
    unittest.main()
