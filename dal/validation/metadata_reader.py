"""
Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import re
from typing import Dict, List, Set

from movai_core_shared.exceptions import DoesNotExist

from dal.movaidb import MovaiDB
from dal.movaidb.db_schema import DBSchema


class MetadataReader:
    """
    Reads metadata documents during one validation run.

    Each attribute of a document is stored in its own Redis key, so finding the keys of one
    document takes a SCAN of the whole keyspace.

    This reader scans each scope once,
    indexes the keys by document, and then reads each document with a single MGET.
    """

    def __init__(self):
        self._db = MovaiDB()
        # {scope: {ref: [keys]}}
        self._keys: Dict[str, Dict[str, List[str]]] = {}
        # {scope: {attribute: type}} of the top level attributes, defaulted like Scope.get_dict()
        self._attributes: Dict[str, Dict[str, str]] = {}

    def index(self, scope: str) -> None:
        """Scan the keyspace once and index the keys of every document of a scope."""

        keys_by_ref: Dict[str, Set[str]] = {}
        for key in self._db.db_read.scan_iter(f"{scope}:*", count=1000):
            key = key.decode("utf-8")
            # Keys have the format <scope>:<ref>,<attribute>...
            ref = re.split("[:,]", key)[1]
            # SCAN can return the same key more than once
            keys_by_ref.setdefault(ref, set()).add(key)

        self._keys[scope] = {ref: sorted(keys, key=str.lower) for ref, keys in keys_by_ref.items()}
        self._attributes[scope] = {
            attr: attr_type
            for attr, attr_type in DBSchema()[scope]["$name"].items()
            if not isinstance(attr_type, dict)
        }

    def refs(self, scope: str) -> Set[str]:
        """Return the names of all documents of an indexed scope."""

        return set(self._keys.get(scope, {}))

    def get_dict(self, scope: str, ref: str) -> dict:
        """Read a document of an indexed scope, in the same format as Scope.get_dict()."""

        try:
            keys = self._keys[scope][ref]
        except KeyError as e:
            raise DoesNotExist(f"{scope} {ref} does not exist") from e

        result = self._db.get_from_keys(keys)
        document = result[scope][ref]
        for attr, attr_type in self._attributes[scope].items():
            if attr not in document:
                document[attr] = [] if attr_type == "list" else {} if attr_type == "hash" else ""

        return result
