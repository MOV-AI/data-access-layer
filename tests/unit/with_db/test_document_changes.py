import time

import pytest


def _wait_subscribed(tracker, after_generation=0, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if tracker._subscribed and tracker._generation > after_generation:
            return
        time.sleep(0.05)
    raise AssertionError("tracker did not subscribe to keyspace notifications")


@pytest.fixture()
def replica_pool(docker_ip, global_db):
    """Connections to a replica of the test master, following it."""

    from redis import ConnectionPool, Redis

    pool = ConnectionPool(host=docker_ip, port=6382, db=0)
    replica = Redis(connection_pool=pool)
    replica.slaveof("redis-master", 6379)
    _wait_replica_link(replica)
    yield pool
    replica.slaveof("redis-master", 6379)


def _wait_replica_link(replica, timeout=20.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if replica.info("replication").get("master_link_status") == "up":
            return
        time.sleep(0.1)
    raise AssertionError("replica did not connect to the master")


class TestDocumentChanges:
    def test_track_changes(self, global_db):
        """Tests that changed documents of the tracked scopes are reported."""

        from dal.movaidb.document_changes import DocumentChangeTracker

        global_db.db_write.config_set("notify-keyspace-events", "AKE")
        tracker = DocumentChangeTracker(["Node"])
        tracker.RETRY_INTERVAL = 0.1
        try:
            # nothing to compare with yet
            assert tracker.take_changes() is None
            assert tracker.take_changes() == set()

            global_db.set({"Node": {"tracked_node": {"Label": "tracked_node"}}})
            global_db.set({"Flow": {"untracked_flow": {"Label": "untracked_flow"}}})
            assert tracker.take_changes() == {("Node", "tracked_node")}
            assert tracker.take_changes() == set()

            global_db.unsafe_delete({"Node": {"tracked_node": "**"}})
            assert tracker.take_changes() == {("Node", "tracked_node")}

            # notifications are lost while not subscribed
            generation = tracker._generation
            global_db.db_write.client_kill_filter(_type="pubsub")
            assert tracker.take_changes() is None
            _wait_subscribed(tracker, after_generation=generation)
            # the first take after subscribing again has nothing to compare with
            tracker.take_changes()
            assert tracker.take_changes() == set()
        finally:
            tracker.close()
            global_db.unsafe_delete({"Flow": {"untracked_flow": "**"}})

    def test_track_changes_without_notifications(self, global_db):
        """Tests that changes are reported as unknown when Redis does not notify them."""

        from dal.movaidb.document_changes import DocumentChangeTracker

        global_db.db_write.config_set("notify-keyspace-events", "")
        tracker = DocumentChangeTracker(["Node"])
        try:
            assert tracker.take_changes() is None
            assert tracker.take_changes() is None
        finally:
            tracker.close()
            global_db.db_write.config_set("notify-keyspace-events", "AKE")


class TestDocumentChangesFromReplica:
    def test_changes_are_in_the_replica_when_taken(self, global_db, replica_pool):
        """Tests that changes taken from the master are already in the replica read."""

        from redis import Redis
        from dal.movaidb import Redis as RedisPools
        from dal.movaidb.document_changes import DocumentChangeTracker

        global_db.db_write.config_set("notify-keyspace-events", "AKE")
        master_pool = RedisPools().master_pool
        replica = Redis(connection_pool=replica_pool)
        tracker = DocumentChangeTracker(["Node"], master_pool, replica_pool)
        try:
            assert tracker.take_changes() is None
            assert tracker.take_changes() == set()

            for value in range(20):
                global_db.set({"Node": {"replicated_node": {"Label": f"label {value}"}}})
                assert tracker.take_changes() == {("Node", "replicated_node")}
                key = "Node:replicated_node,Label:"
                assert replica.get(key) == global_db.db_write.get(key)
        finally:
            tracker.close()
            global_db.unsafe_delete({"Node": {"replicated_node": "**"}})

    def test_changes_are_kept_while_the_replica_is_not_in_sync(self, global_db, replica_pool):
        """Tests that changes are not lost while the replica read does not follow the master."""

        from redis import Redis
        from dal.movaidb import Redis as RedisPools
        from dal.movaidb.document_changes import DocumentChangeTracker

        global_db.db_write.config_set("notify-keyspace-events", "AKE")
        replica = Redis(connection_pool=replica_pool)
        tracker = DocumentChangeTracker(["Node"], RedisPools().master_pool, replica_pool)
        tracker.REPLICA_TIMEOUT = 0.2
        try:
            tracker.take_changes()
            assert tracker.take_changes() == set()

            replica.slaveof()  # no longer a replica
            global_db.set({"Node": {"unsynced_node": {"Label": "unsynced"}}})
            assert tracker.take_changes() is None

            replica.slaveof("redis-master", 6379)
            _wait_replica_link(replica)
            assert ("Node", "unsynced_node") in tracker.take_changes()
        finally:
            tracker.close()
            global_db.unsafe_delete({"Node": {"unsynced_node": "**"}})
