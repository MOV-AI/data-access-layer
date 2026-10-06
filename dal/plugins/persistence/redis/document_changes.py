"""
Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import threading
import uuid
from typing import Dict, Iterable, Optional, Set, Tuple

from movai_core_shared.logger import Log
from redis.client import ConnectionPool, Redis

LOGGER = Log.get_logger(__name__)


class DocumentChangeTracker:
    """
    Tracks the documents of some scopes that change in Redis, using keyspace notifications.

    Each attribute of a document is stored in a key "<scope>:<ref>,...", so every write to a
    document notifies keys with that prefix. A background thread subscribes to those
    notifications and records the documents that changed until take_changes() is called.

    Notifications sent while the thread is not subscribed are lost, and a replica that
    resynchronizes with its master loads data without notifying it. take_changes() only
    returns the changes when it can tell none were missed since its previous call, and
    None otherwise, in which case any document may have changed.
    """

    # Seconds to wait for the notifications sent before take_changes() to be received
    SYNC_TIMEOUT = 2.0
    # Seconds between attempts to subscribe after a failure
    RETRY_INTERVAL = 5.0

    def __init__(self, connection_pool: ConnectionPool, scopes: Iterable[str]):
        self._pool = connection_pool
        self._db = connection_pool.connection_kwargs.get("db", 0)
        self._patterns = [f"__keyspace@{self._db}__:{scope}:*" for scope in scopes]
        # Messages published here are received after every notification sent before them
        self._sync_channel = f"movai:document_changes:sync:{uuid.uuid4().hex}"

        self._lock = threading.Lock()
        self._changes: Set[Tuple[str, str]] = set()
        # Increases with every new subscription, notifications may be lost between two of them
        self._generation = 0
        self._subscribed = False
        # Generation of the subscription that saw every change since the last take_changes()
        self._complete_generation: Optional[int] = None
        self._pending_syncs: Dict[str, threading.Event] = {}
        # Set when a sync message is not received, the subscription may be silently broken
        self._reconnect = threading.Event()
        self._closed = threading.Event()
        # Failures are only logged when they start
        self._failing = False
        # Set once the first attempt to subscribe succeeds or fails
        self._first_attempt = threading.Event()

        self._thread = threading.Thread(target=self._run, name="DocumentChangeTracker", daemon=True)
        self._thread.start()

    def take_changes(self) -> Optional[Set[Tuple[str, str]]]:
        """
        Return the (scope, ref) of the documents that changed since the previous call,
        or None if changes may have been missed, and start recording again.
        """
        generation = self._sync()

        with self._lock:
            complete = generation is not None and generation == self._complete_generation
            changes = self._changes if complete else None
            self._changes = set()
            # after a None the caller reloads everything, so from now on nothing was missed
            self._complete_generation = generation

        return changes

    def close(self):
        """Stop tracking changes."""
        self._closed.set()

    def _sync(self) -> Optional[int]:
        """
        Wait until the notifications sent so far have been received, returning the
        generation of the subscription that received them, or None if not possible.
        """
        # right after starting, wait for the subscription instead of reporting missed changes
        self._first_attempt.wait(self.SYNC_TIMEOUT)

        token = uuid.uuid4().hex
        received = threading.Event()
        with self._lock:
            if not self._subscribed:
                return None
            generation = self._generation
            self._pending_syncs[token] = received

        try:
            conn = Redis(connection_pool=self._pool)
            if conn.info("replication").get("role") != "master":
                # a replica that resynchronizes loads data without notifying it
                return None
            conn.publish(self._sync_channel, token)
            if not received.wait(self.SYNC_TIMEOUT):
                LOGGER.warning("Timed out waiting for document change notifications")
                with self._lock:
                    # only if a newer subscription has not replaced the silent one
                    if self._subscribed and self._generation == generation:
                        self._reconnect.set()
                return None
        except Exception as error:  # pylint: disable=broad-except
            LOGGER.warning(f"Could not check for document changes: {error}")
            return None
        finally:
            with self._lock:
                self._pending_syncs.pop(token, None)

        with self._lock:
            if self._subscribed and self._generation == generation:
                return generation
        return None

    def _run(self):
        """Keep a subscription to the notifications, subscribing again when it fails."""
        while not self._closed.is_set():
            try:
                self._listen()
            except Exception as error:  # pylint: disable=broad-except
                if not self._failing:
                    LOGGER.warning(f"Not tracking document changes: {error}")
                self._failing = True
                self._first_attempt.set()
            finally:
                with self._lock:
                    self._subscribed = False

            self._closed.wait(self.RETRY_INTERVAL)

    def _listen(self):
        """Subscribe to the notifications and record them, until closed or failing."""
        conn = Redis(connection_pool=self._pool)
        flags = conn.config_get("notify-keyspace-events").get("notify-keyspace-events", "")
        # K: keyspace channels, A: all events, otherwise generic, string, hash and list events
        if "K" not in flags or ("A" not in flags and not all(event in flags for event in "g$hl")):
            raise RuntimeError(f"Redis keyspace notifications are disabled ('{flags}')")

        pubsub = conn.pubsub()
        try:
            pubsub.psubscribe(*self._patterns)
            pubsub.subscribe(self._sync_channel)
            confirmations = len(self._patterns) + 1

            while not self._closed.is_set():
                if self._reconnect.is_set():
                    raise ConnectionError("sync message not received")

                message = pubsub.get_message(timeout=1.0)
                if message is None:
                    continue

                if message["type"] in ("psubscribe", "subscribe"):
                    confirmations -= 1
                    if confirmations == 0:
                        with self._lock:
                            self._generation += 1
                            self._subscribed = True
                            self._reconnect.clear()
                        self._first_attempt.set()
                        if self._failing:
                            LOGGER.info("Tracking document changes again")
                        self._failing = False
                elif message["type"] == "pmessage":
                    self._record(message["channel"])
                elif message["type"] == "message":
                    self._release_sync(message["data"])
        finally:
            pubsub.close()

    def _record(self, channel: bytes):
        """Record the document of a key notification, "__keyspace@<db>__:<scope>:<ref>,..." """
        key = channel.decode("utf-8", errors="replace").split(":", 1)[1]
        scope, _, rest = key.partition(":")
        ref = rest.partition(",")[0]
        with self._lock:
            self._changes.add((scope, ref))

    def _release_sync(self, data: bytes):
        """Wake up the take_changes() waiting for this sync message."""
        with self._lock:
            received = self._pending_syncs.get(data.decode("utf-8", errors="replace"))
        if received is not None:
            received.set()
