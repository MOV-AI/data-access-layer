from time import sleep


class TestMovaiDB:
    def test_db(self, global_db):
        """Write and read"""
        node = {"Node": {"hi": "*"}}
        node_data = {"Node": {"hi": {"Label": "hi", "User": "movai"}}}
        global_db.set(node_data)
        sleep(0.01)  # ensure the data is written before reading
        assert node_data == global_db.get(node)

    def test_ttl(self, global_db, scopes_robot):
        """Robot fleet parameter TTL"""
        scopes_robot.fleet.add("Parameter", "on_set", Value=10.0, TTL=1)
        # expire only happens once value is set after TTL
        scopes_robot.fleet.Parameter["on_set"].TTL = 1
        scopes_robot.fleet.Parameter["on_set"].Value = 20

        sleep(1.5)

        assert scopes_robot.fleet.Parameter["on_set"].Value is None

    def test_ttl_on_add(self, global_db, scopes_robot):
        """Robot fleet parameter TTL"""
        scopes_robot.fleet.add("Parameter", "on_add", Value=10.0, TTL=1)

        sleep(1.5)

        assert scopes_robot.fleet.Parameter["on_add"].Value is None

    def test_read_keys_of_any_type(self, global_db):
        """Tests that keys of each type are read, and kept by get_from_keys like before."""

        db = global_db.db_write
        prefix = "Node:read_keys_test"
        keys = {
            "string": f"{prefix},Label:",
            "empty": f"{prefix},Info:",
            "hash": f"{prefix},Hash:",
            "list": f"{prefix},List:",
            "set": f"{prefix},Set:",
            "missing": f"{prefix},Missing:",
        }
        db.set(keys["string"], "label")
        db.set(keys["empty"], "")
        db.hset(keys["hash"], "b", "2")
        db.hset(keys["hash"], "a", "1")
        db.rpush(keys["list"], "x", "y")
        db.sadd(keys["set"], "member")
        try:
            values = global_db.read_keys(global_db.db_read, list(keys.values()))
            assert values[keys["string"]] == ("get", b"label")
            assert values[keys["empty"]] == ("get", b"")
            assert values[keys["hash"]] == ("hgetall", {b"a": b"1", b"b": b"2"})
            assert values[keys["list"]] == ("lrange", [b"x", b"y"])
            assert values[keys["set"]] == (None, None)
            assert values[keys["missing"]] == ("get", None)

            document = global_db.get_from_keys(list(keys.values()))["Node"]["read_keys_test"]
            # empty strings and keys of other types are not read, missing keys read as a hash
            assert document == {
                "Label": "label",
                "Hash": {"a": "1", "b": "2"},
                "List": ["x", "y"],
                "Missing": {},
            }
            assert list(document["Hash"]) == ["a", "b"]
        finally:
            db.delete(*keys.values())
