import os
import pytest
import sys
import importlib
import time


from pathlib import Path

CURR_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
METADATA_FOLDER = CURR_DIR / "data" / "metadata"
MANIFEST_FILE = CURR_DIR / "data" / "manifest.txt"
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
    return METADATA_FOLDER


@pytest.fixture(scope="session")
def manifest_file():
    return MANIFEST_FILE
