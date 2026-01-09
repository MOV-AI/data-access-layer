from time import sleep
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dal.movaidb.database import MovaiDB
    from dal.scopes.robot import Robot


class TestMovaiDB:
    def test_db(self, global_db: "MovaiDB"):
        """Write and read"""
        node = {"Node": {"hi": "*"}}
        node_data = {"Node": {"hi": {"Label": "hi", "User": "movai"}}}
        global_db.set(node_data)
        sleep(0.01)  # ensure the data is written before reading
        assert node_data == global_db.get(node)

    def test_ttl(self, global_db, scopes_robot: "Robot"):
        """Robot fleet parameter TTL"""
        scopes_robot.fleet.add("Parameter", "on_set", Value=10.0, TTL=1)
        # expire only happens once value is set after TTL
        scopes_robot.fleet.Parameter["on_set"].TTL = 1
        scopes_robot.fleet.Parameter["on_set"].Value = 20

        sleep(1.5)

        assert scopes_robot.fleet.Parameter["on_set"].Value is None

    def test_ttl_on_add(self, global_db, scopes_robot: "Robot"):
        """Robot fleet parameter TTL"""
        scopes_robot.fleet.add("Parameter", "on_add", Value=10.0, TTL=1)

        sleep(1.5)

        assert scopes_robot.fleet.Parameter["on_add"].Value is None
