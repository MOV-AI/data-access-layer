import os
import pytest


from pathlib import Path

CURR_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
METADATA_FOLDER = CURR_DIR / "metadata"
DOCKER_COMPOSE = CURR_DIR / "docker-compose.yml"


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return str(DOCKER_COMPOSE)


@pytest.fixture(scope="session", autouse=True)
def set_redis_ip(docker_ip):
    os.environ["REDIS_MASTER_HOST"] = docker_ip
    os.environ["REDIS_MASTER_PORT"] = "6380"

    os.environ["REDIS_LOCAL_HOST"] = docker_ip
    os.environ["REDIS_LOCAL_PORT"] = "6381"


@pytest.fixture(scope="class")
def global_db(set_redis_ip, docker_services):
    from dal.movaidb.database import MovaiDB

    return MovaiDB()


@pytest.fixture(scope="class")
def scopes_robot(global_db):
    from dal.scopes.robot import Robot

    return Robot()


@pytest.fixture(scope="class")
def models_message(global_db):
    from dal.models.message import Message

    return Message
