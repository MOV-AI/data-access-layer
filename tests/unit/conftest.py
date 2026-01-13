import os
import pytest
import sys
import importlib
import time


from pathlib import Path

CURR_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
DATA_FOLDER = CURR_DIR / "data"
DOCKER_COMPOSE = CURR_DIR / "docker-compose.yml"


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return str(DOCKER_COMPOSE)


@pytest.fixture(scope="session")
def set_redis_ip(docker_ip):
    os.environ["REDIS_MASTER_HOST"] = docker_ip
    os.environ["REDIS_MASTER_PORT"] = "6380"

    os.environ["REDIS_LOCAL_HOST"] = docker_ip
    os.environ["REDIS_LOCAL_PORT"] = "6381"

    # there are mocks leaking to other tests, so we need to reload redis
    for key in list(sys.modules):
        if key.startswith("redis"):
            importlib.reload(sys.modules[key])
    # reload modules which use env vars
    for key in list(sys.modules):
        if key.startswith("movai_core_shared"):
            importlib.reload(sys.modules[key])
    for key in list(sys.modules):
        if key.startswith("dal"):
            importlib.reload(sys.modules[key])


@pytest.fixture(scope="session")
def global_db(set_redis_ip, docker_services):
    from dal.movaidb.database import MovaiDB

    db = MovaiDB()
    time.sleep(2)  # wait for db to be ready
    return db


@pytest.fixture(scope="session")
def scopes_robot(global_db):
    from dal.scopes.robot import Robot

    robot = Robot()
    return robot


@pytest.fixture(scope="session")
def models_message(global_db):
    from dal.models.message import Message

    msg = Message
    return msg


@pytest.fixture(scope="session")
def metadata_folder():
    return DATA_FOLDER / "valid" / "metadata"


@pytest.fixture(scope="session")
def metadata2_folder():
    return DATA_FOLDER / "valid" / "metadata2"


@pytest.fixture(scope="session")
def manifest_file():
    return DATA_FOLDER / "valid" / "manifest.txt"


@pytest.fixture(scope="session")
def metadata_folder_invalid_data():
    return DATA_FOLDER / "invalid" / "metadata"


@pytest.fixture(scope="session")
def manifest_file_invalid_data():
    return DATA_FOLDER / "invalid" / "manifest.txt"


@pytest.fixture
def delete_all_robots(global_db):
    """Deletes all robots after test."""
    from dal.scopes.robot import Robot, FleetRobot

    yield

    Robot().remove()

    for robot_id in Robot.get_all():
        FleetRobot.remove_entry(robot_id, True)


@pytest.fixture()
def setup_test_data(global_db, metadata_folder):
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
