"""Tests for the Schema class."""
import pytest
from pathlib import Path
import urllib.parse

from dal.validation import Schema
from dal.validation import JSON_SCHEMA_FOLDER_PATH
from dal.classes.filesystem import FileSystem


@pytest.fixture
def translation_validator():
    clean_path = urllib.parse.urlparse(JSON_SCHEMA_FOLDER_PATH).path
    path = Path(clean_path) / "2.4" / "Translation.schema.json"
    return Schema(path)


@pytest.fixture
def translation_valid_data(metadata_folder):
    data = FileSystem.read_json(metadata_folder / "Translation" / "delete_me.json")
    return data["Translation"]["delete_me"]


@pytest.fixture
def translation_invalid_data(metadata_folder_invalid_data):
    data = FileSystem.read_json(metadata_folder_invalid_data / "Translation" / "delete_me.json")
    return data["Translation"]["delete_me"]


@pytest.fixture
def alert_validator():
    clean_path = urllib.parse.urlparse(JSON_SCHEMA_FOLDER_PATH).path
    path = Path(clean_path) / "2.4" / "Alert.schema.json"
    return Schema(path)


@pytest.fixture
def alert_valid_data(metadata_folder):
    data = FileSystem.read_json(metadata_folder / "Alert" / "delete_me.json")
    return data["Alert"]["delete_me"]


@pytest.fixture
def alert_invalid_data(metadata_folder_invalid_data):
    data = FileSystem.read_json(metadata_folder_invalid_data / "Alert" / "delete_me.json")
    return data["Alert"]["delete_me"]


@pytest.fixture
def node_validator():
    clean_path = urllib.parse.urlparse(JSON_SCHEMA_FOLDER_PATH).path
    path = Path(clean_path) / "2.4" / "Node.schema.json"
    return Schema(path)


@pytest.fixture
def node_valid_data(metadata_folder):
    data = FileSystem.read_json(metadata_folder / "Node" / "delete_me.json")
    return data["Node"]["delete_me"]


@pytest.fixture
def node_invalid_data(metadata_folder_invalid_data):
    data = FileSystem.read_json(metadata_folder_invalid_data / "Node" / "delete_me.json")
    return data["Node"]["delete_me"]


class TestTranslationSchema:
    def test_validate(self, translation_validator, translation_valid_data):
        """Test that valid data passes validation."""
        res = translation_validator.validate(translation_valid_data)
        assert res["status"] is True, res["message"]

    def test_validate_negative(self, translation_validator, translation_invalid_data):
        """Test that invalid data fails validation."""
        res = translation_validator.validate(translation_invalid_data)
        assert res["status"] is False
        assert "invalid_data" in res["message"]


class TestAlertSchema:
    def test_validate(self, alert_validator, alert_valid_data):
        """Test that valid data passes validation."""
        res = alert_validator.validate(alert_valid_data)
        assert res["status"] is True, res["message"]

    def test_validate_negative(self, alert_validator, alert_invalid_data):
        """Test that invalid data fails validation."""
        res = alert_validator.validate(alert_invalid_data)
        assert res["status"] is False
        assert "invalid_data" in res["message"]


class TestNodeSchema:
    def test_validate(self, node_validator, node_valid_data):
        """Test that valid data passes validation."""
        res = node_validator.validate(node_valid_data)
        assert res["status"] is True, res["message"]

    def test_validate_negative(self, node_validator, node_invalid_data):
        """Test that invalid data fails validation."""
        res = node_validator.validate(node_invalid_data)
        assert res["status"] is False
        assert "invalid_data" in res["message"]

    def test_validate_ros1_node_ros2_port(self):
        """Test that a ROS1 node with a ROS2 port fails validation."""
        from dal.scopes.node import Node

        data = {
            "Type": "ROS1/Node",
            "PortsInst": {
                "pubport": {
                    "Message": "Float32",
                    "Out": {"out": {"Message": "std_msgs/Float32"}},
                    "Package": "std_msgs",
                    "Template": "ROS2/Publisher",
                }
            },
        }

        with pytest.raises(ValueError, match="ROS1/Node nodes cannot have"):
            Node.validate_format("Node", data)

    def test_validate_ros2_node_ros1_port(self):
        """Test that a ROS2 node with a ROS1 port fails validation."""
        from dal.scopes.node import Node

        data = {
            "Type": "ROS2/Node",
            "PortsInst": {
                "pubport": {
                    "Message": "Float32",
                    "Out": {"out": {"Message": "std_msgs/Float32"}},
                    "Package": "std_msgs",
                    "Template": "ROS1/Publisher",
                }
            },
        }

        with pytest.raises(ValueError, match="ROS2/Node nodes cannot have"):
            Node.validate_format("Node", data)

    def test_validate_ros1_node_transition_port(self):
        """Test that a ROS1 node with a transition port fails validation."""
        from dal.scopes.node import Node

        data = {
            "Type": "ROS1/Node",
            "PortsInst": {
                "start": {
                    "In": {
                        "in": {"Callback": "create_log_start", "Message": "movai_msgs/Transition"}
                    },
                    "Message": "Transition",
                    "Package": "movai_msgs",
                    "Template": "MovAI/TransitionTo",
                }
            },
        }

        with pytest.raises(ValueError, match="ROS1/Node nodes cannot have"):
            Node.validate_format("Node", data)

    def test_validate_ros1_node_plugin_client_port(self):
        """Test that a ROS1 node with a plugin client port fails validation."""
        from dal.scopes.node import Node

        data = {
            "Type": "ROS1/Node",
            "PortsInst": {
                "test": {
                    "Info": "",
                    "Message": "Plugin",
                    "Out": {"out": {"Message": "movai_msgs/Plugin"}},
                    "Package": "movai_msgs",
                    "Template": "ROS1/PluginClient",
                }
            },
        }

        with pytest.raises(ValueError, match="ROS1/Node nodes cannot have"):
            Node.validate_format("Node", data)

    def test_validate_ros1_node_nodelet_client_port(self):
        """Test that a ROS1 node with a nodelet client port fails validation."""
        from dal.scopes.node import Node

        data = {
            "Type": "ROS1/Node",
            "PortsInst": {
                "test": {
                    "In": {"in": {"Message": "movai_msgs/Nodelet"}},
                    "Info": "",
                    "Message": "Nodelet",
                    "Package": "movai_msgs",
                    "Template": "ROS1/NodeletServer",
                }
            },
        }

        with pytest.raises(ValueError, match="ROS1/Node nodes cannot have"):
            Node.validate_format("Node", data)

    def test_validate_ros1_node_http_port(self):
        """Test that a ROS1 node with an HTTP port fails validation."""
        from dal.scopes.node import Node

        data = {
            "Type": "ROS1/Node",
            "PortsInst": {
                "test": {
                    "In": {
                        "data_in": {
                            "Callback": "place_holder",
                            "Message": "movai_msgs/Http",
                            "Parameter": {"Endpoint": "http"},
                        }
                    },
                    "Info": "",
                    "Message": "Http",
                    "Package": "movai_msgs",
                    "Template": "AioHttp/Http",
                }
            },
        }

        with pytest.raises(ValueError, match="ROS1/Node nodes cannot have"):
            Node.validate_format("Node", data)
