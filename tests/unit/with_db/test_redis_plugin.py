import time
import pytest


KEYS = [
    "Flow:main,Label:",
    "Flow:main,NodeInst:pub,Template:",
    "Flow:main,NodeInst:pub,Parameter:rate,Value:",
    "Flow:main,NodeInst:sub,Parameter:topic,Value:",
    "Flow:main,Container:child,Parameter:rate,Value:",
    "Flow:main,Links:a1b2,From:",
    "Flow:main,ExposedPorts:pub:pub/out/out",
    "Flow:main_other,Label:",
]


def _wait_subscribed(tracker, after_generation=0, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if tracker._subscribed and tracker._generation > after_generation:
            return
        time.sleep(0.05)
    raise AssertionError("tracker did not subscribe to keyspace notifications")


class TestRedisPlugin:
    def test_batch_reads_match_reads(self, setup_test_data):
        """Tests that documents read in batch_reads() are the same as read one by one."""

        from dal.models.scopestree import scopes

        plugin = scopes().plugin
        documents = [
            (scope, obj["ref"])
            for scope in ("Flow", "Node", "Callback")
            for obj in plugin.list_scopes(scope=scope, workspace="global")
        ]
        assert documents, "Expected test data"

        unbatched = {doc: plugin.read(scope=doc[0], ref=doc[1]) for doc in documents}
        with plugin.batch_reads():
            batched = {doc: plugin.read(scope=doc[0], ref=doc[1]) for doc in documents}
            missing = plugin.read(scope="Flow", ref="non_existing_flow")

        assert batched == unbatched
        # same order too, it decides the order of the objects loaded from the documents
        assert [repr(batched[doc]) for doc in documents] == [
            repr(unbatched[doc]) for doc in documents
        ]
        assert missing == {"schema_version": "1.0"}

    def test_track_changes(self, global_db):
        """Tests that changed documents of the tracked scopes are reported."""

        from dal.models.scopestree import scopes

        global_db.db_write.config_set("notify-keyspace-events", "AKE")
        tracker = scopes().plugin.track_changes(["Node"])
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

        from dal.models.scopestree import scopes

        global_db.db_write.config_set("notify-keyspace-events", "")
        tracker = scopes().plugin.track_changes(["Node"])
        try:
            assert tracker.take_changes() is None
            assert tracker.take_changes() is None
        finally:
            tracker.close()
            global_db.db_write.config_set("notify-keyspace-events", "AKE")

    def test_unload_all_keep_scopes(self, setup_test_data):
        """Tests that unload_all() keeps the documents of the scopes asked for."""

        from dal.models.scopestree import scopes

        workspace = scopes()
        node_ref = workspace.list_scopes(scope="Node")[0]["ref"]
        flow_ref = workspace.list_scopes(scope="Flow")[0]["ref"]
        node = scopes.from_path(node_ref, scope="Node")
        flow = scopes.from_path(flow_ref, scope="Flow")

        workspace.unload_all(keep_scopes=["Node"])

        assert scopes.from_path(node_ref, scope="Node") is node
        assert scopes.from_path(flow_ref, scope="Flow") is not flow

    def test_loaded_refs(self, setup_test_data):
        """Tests that loaded_refs() lists the documents loaded in the workspace."""

        from dal.models.scopestree import scopes

        workspace = scopes()
        node_ref = workspace.list_scopes(scope="Node")[0]["ref"]
        workspace.unload_all()
        assert node_ref not in workspace.loaded_refs("Node")

        scopes.from_path(node_ref, scope="Node")
        assert node_ref in workspace.loaded_refs("Node")

        workspace.unload(scope="Node", ref=node_ref)
        assert node_ref not in workspace.loaded_refs("Node")
        assert workspace.loaded_refs("NotAScope") == []


@pytest.mark.parametrize(
    "document, pattern",
    [
        ("Flow:main", "Flow:main,Label:"),
        ("Flow:main", "Flow:main,NodeInst:*,Template:"),
        ("Flow:main", "Flow:main,NodeInst:*,Parameter:*,Value:"),
        ("Flow:main", "Flow:main,*,Parameter:*,Value:"),
        ("Flow:main", "Flow:main,ExposedPorts:*"),
        ("Flow:main", "Flow:main,Links:*,From:"),
        ("Flow:main", "Flow:other,Label:"),
        ("Flow:ma*", "Flow:ma*,Label:"),
    ],
)
def test_filter_keys_matches_fnmatch(document, pattern):
    """Tests that keys are matched like fnmatch.filter, in the same order."""
    from dal.plugins.persistence.redis.redis import RedisPlugin
    import fnmatch

    plugin = RedisPlugin(workspace="global")
    assert plugin._filter_keys(KEYS, pattern, document) == fnmatch.filter(KEYS, pattern)
