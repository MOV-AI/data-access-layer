from abc import ABC, abstractmethod
import json
import os
import re
from typing import Iterator, List, Optional, Tuple

from movai_core_shared.exceptions import ImportException

PLACEHOLDER_RE = re.compile(r"(/)?place_holder(?(1)(/|$)|)")
CONFIG_RE = re.compile(r"^\$\(\s*config\s+([${}a-zA-Z0-9_]+)\.?.*\)$")
ENV_RE = re.compile(r"\$\{?(.+?)\}?$")


def from_path(name):
    try:
        from dal.models.scopestree import scopes

        return scopes.extract_reference(name)[2]
    except KeyError:
        # not a path and `scope` wasn't passed
        # we don't care
        return name


class ProjectSource(ABC):
    """Project metadata source addressed by project-relative POSIX paths.

    Importer historically reads from a project folder on disk. This interface
    keeps the importer talking in relative paths like ``Callback/foo.json`` so
    another source, such as a gRPC payload, can provide the same files without
    recreating that folder on the filesystem.
    """

    @staticmethod
    def normalize_path(relative_path: str) -> str:
        """Normalize and validate a source-relative path."""
        if relative_path is None:
            raise ValueError("relative_path cannot be None")

        path = str(relative_path).replace("\\", "/")
        if os.path.isabs(path):
            raise ValueError(f"absolute paths are not allowed: {relative_path}")

        normalized = os.path.normpath(path).replace("\\", "/")
        if normalized == ".":
            return ""
        if normalized == ".." or normalized.startswith("../"):
            raise ValueError(f"path escapes project source: {relative_path}")

        return normalized

    @staticmethod
    def join(*parts: str) -> str:
        """Join path parts into a normalized source-relative path."""
        return ProjectSource.normalize_path(
            "/".join(str(part).strip("/") for part in parts if part)
        )

    def _list_scope(self, scope: str, directories: bool = False) -> List[Tuple[str, str]]:
        """Lists either directories or .json files in the given scope."""
        try:
            entries = self.list_dir(scope)
        except FileNotFoundError:
            return []

        results = []
        for entry in entries:
            full_path = ProjectSource.join(scope, entry)

            if directories:
                if self.is_dir(full_path):
                    results.append((entry, full_path))
            else:
                if entry.endswith(".json"):
                    identifier = os.path.splitext(entry)[0]
                    results.append((identifier, full_path))

        return results

    def _get_by_names(
        self, scope: str, names: List[str], directories: bool = False
    ) -> List[Tuple[str, str]]:
        """Resolves specific directories or .json files by name."""
        if not names:
            return []

        if not self.is_dir(scope):
            ImportException(f"{scope} directory not found")
            return []

        results = []
        for raw_name in names:
            name = from_path(raw_name)
            filename = name if directories else f"{name}.json"
            full_path = ProjectSource.join(scope, filename)

            is_valid = self.is_dir(full_path) if directories else self.is_file(full_path)

            if not is_valid:
                ImportException(f"{scope}:{name} not found")
                continue

            results.append((name, full_path))

        return results

    def get_files(
        self,
        scope: str,
        names: Optional[List[str]] = None,
        directories: bool = False,
    ) -> List[Tuple[str, str]]:
        """Resolves items in scope. Defaults to .json files; sets directories=True for folders."""
        if names is None:
            return self._list_scope(scope, directories)
        return self._get_by_names(scope, names, directories)

    def _read_json(self, relative_path: str) -> dict:
        """Read a JSON file from the configured project source."""
        return json.loads(self.read_text(relative_path))

    @abstractmethod
    def list_dir(self, relative_dir: str) -> List[str]:
        """Return direct child names for a source-relative directory."""

    @abstractmethod
    def is_file(self, relative_path: str) -> bool:
        """Return whether the source-relative path is a regular file."""

    @abstractmethod
    def is_dir(self, relative_path: str) -> bool:
        """Return whether the source-relative path is a directory."""

    @abstractmethod
    def read_text(self, relative_path: str) -> str:
        """Read a source-relative file as UTF-8 text."""

    @abstractmethod
    def read_bytes(self, relative_path: str) -> bytes:
        """Read a source-relative file as bytes."""

    @abstractmethod
    def walk(self, relative_dir: str) -> Iterator[Tuple[str, List[str], List[str]]]:
        """Yield ``(relative_root, dirs, files)`` for a source-relative directory."""

    @abstractmethod
    def display_path(self, relative_path: str) -> str:
        """Return a human-readable path for logs and imported InstallPath."""


class FilesystemProjectSource(ProjectSource):
    """Filesystem-backed project source."""

    def __init__(self, root: str):
        self.root = os.path.abspath(root)

    def _resolve(self, relative_path: str) -> str:
        normalized = self.normalize_path(relative_path)
        resolved = os.path.abspath(os.path.join(self.root, normalized))

        try:
            common_path = os.path.commonpath([self.root, resolved])
        except ValueError as exc:
            raise ValueError(f"path escapes project source: {relative_path}") from exc

        if common_path != self.root:
            raise ValueError(f"path escapes project source: {relative_path}")

        return resolved

    def list_dir(self, relative_dir: str) -> List[str]:
        return os.listdir(self._resolve(relative_dir))

    def is_file(self, relative_path: str) -> bool:
        return os.path.isfile(self._resolve(relative_path))

    def is_dir(self, relative_path: str) -> bool:
        return os.path.isdir(self._resolve(relative_path))

    def read_text(self, relative_path: str) -> str:
        with open(self._resolve(relative_path), encoding="utf-8") as file:
            return file.read()

    def read_bytes(self, relative_path: str) -> bytes:
        with open(self._resolve(relative_path), "rb") as file:
            return file.read()

    def walk(self, relative_dir: str) -> Iterator[Tuple[str, List[str], List[str]]]:
        start = self._resolve(relative_dir)
        for root, dirs, files in os.walk(start):
            relative_root = os.path.relpath(root, self.root)
            if relative_root == ".":
                relative_root = ""
            yield relative_root.replace("\\", "/"), dirs, files

    def display_path(self, relative_path: str) -> str:
        return self._resolve(relative_path)


class InMemoryProjectSource(ProjectSource):
    """In-memory project source for gRPC payloads."""

    def __init__(self, files: dict):
        self.files = {}
        for path, content in files.items():
            normalized = self.normalize_path(path)
            if isinstance(content, str):
                content = content.encode("utf-8")
            self.files[normalized] = content

    def list_dir(self, relative_dir: str) -> List[str]:
        prefix = self.normalize_path(relative_dir)
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        children = set()
        for path in self.files:
            if not path.startswith(prefix):
                continue
            children.add(path[len(prefix) :].split("/", 1)[0])

        return sorted(children)

    def is_file(self, relative_path: str) -> bool:
        normalized = self.normalize_path(relative_path)
        return normalized in self.files

    def is_dir(self, relative_path: str) -> bool:
        prefix = self.normalize_path(relative_path)
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        return any(path.startswith(prefix) for path in self.files)

    def read_text(self, relative_path: str) -> str:
        normalized = self.normalize_path(relative_path)
        if normalized not in self.files:
            raise FileNotFoundError(f"File not found: {relative_path}")
        return self.read_bytes(normalized).decode("utf-8")

    def read_bytes(self, relative_path: str) -> bytes:
        normalized = self.normalize_path(relative_path)
        if normalized not in self.files:
            raise FileNotFoundError(f"File not found: {relative_path}")
        return self.files[normalized]

    def walk(self, relative_dir: str):
        """
        Walk the in-memory file structure, yielding (relative_root, dirs, files).
        """
        root = self.normalize_path(relative_dir)
        stack = [root]

        while stack:
            current = stack.pop()
            dirs = []
            files = []

            for path in self.files:
                if not path.startswith(current):
                    continue
                relative_path = path[len(current) :].lstrip("/")
                if "/" in relative_path:
                    dir_name = relative_path.split("/", 1)[0]
                    if dir_name not in dirs:
                        dirs.append(dir_name)
                else:
                    files.append(relative_path)

            yield current, dirs, files

            for dir_name in dirs:
                stack.append(self.join(current, dir_name))

    def display_path(self, relative_path: str) -> str:
        return self.normalize_path(relative_path)
