import os
import pytest
import sys
import importlib
import time


from pathlib import Path

CURR_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
METADATA_FOLDER = CURR_DIR / "metadata"
DOCKER_COMPOSE = CURR_DIR / "docker-compose.yml"


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return str(DOCKER_COMPOSE)


@pytest.fixture(scope="module")
def set_redis_ip(docker_ip):
    os.environ["REDIS_MASTER_HOST"] = docker_ip
    os.environ["REDIS_MASTER_PORT"] = "6380"

    os.environ["REDIS_LOCAL_HOST"] = docker_ip
    os.environ["REDIS_LOCAL_PORT"] = "6381"

    # there are mocks leaking to other tests, so we need to reload redis
    for key in list(sys.modules):
        if key.startswith("redis"):
            try:
                importlib.reload(sys.modules[key])
            except Exception as e:
                pass
    # reload modules which use env vars
    for key in list(sys.modules):
        if key.startswith("movai_core_shared"):
            try:
                importlib.reload(sys.modules[key])
            except Exception as e:
                pass
    for key in list(sys.modules):
        if key.startswith("dal"):
            try:
                importlib.reload(sys.modules[key])
            except Exception as e:
                pass

    time.sleep(0.5)  # wait for db to be ready


@pytest.fixture()
def global_db(set_redis_ip, docker_services):
    from dal.movaidb.database import MovaiDB

    return MovaiDB()


@pytest.fixture()
def scopes_robot(global_db):
    from dal.scopes.robot import Robot

    return Robot()


@pytest.fixture()
def models_message(global_db):
    from dal.models.message import Message

    return Message
