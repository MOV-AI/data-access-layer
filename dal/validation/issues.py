from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import List, Dict


class Severity(Enum):
    """Severity enumeration."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    ERROR = 4

    def __str__(self) -> str:
        """Provides correct casing.

        Returns:
            The severity with the correct casing for Jenkins Warnings Next Generation plugin.

        """

        return self.name.title()


class Issue:
    """Base issue class.

    Attributes:
        category (str): Issue category.
        iss_type (str): Issue type.
        severity (Severity): Issue severity.
        msg (str): Issue message.
        line_start (int): Issue start line.
        line_ranges (Any): Issue line range.

    """

    def __init__(
        self,
        category: str,
        iss_type: str,
        severity: Severity,
        msg: str,
        line_start: int = 0,
        line_ranges: List[Dict[str, int]] = None,
    ) -> None:
        self.category = category
        self.iss_type = iss_type
        self.severity = severity
        self.msg = msg
        self.line_start = line_start
        self.line_ranges = line_ranges

    @abstractmethod
    def __str__(self) -> str:
        """Provides issue string representation.

        Returns:
            The issue string representation.

        """


class ProjIssue(Issue):
    """Project base issue class.

    Attributes:
        json_path (Path): Path to file with issue.
        category (str): Issue category.
        iss_type (str): Issue type.
        severity (Severity): Issue severity.
        msg (str): Issue message.
        line_start (int): Issue start line.
        line_ranges (Any): Issue line range.

    """

    def __str__(self) -> str:
        """Provides issue string representation.

        Returns:
            The issue string representation.

        """

        level = str(self.severity) if self.severity == Severity.ERROR else "Warn"

        return f"[{level}] {self.msg}"


class MissingFlowInstance(ProjIssue):
    """Missing flow instance referenced by link.

    Attributes:
        json_path (Path): Path to file with issue.
        msg (str): Issue message.

    """

    def __init__(
        self,
        json_path: Path,
        msg: str,
    ) -> None:
        self.json_path = json_path

        super().__init__(
            "Formating",
            "Missing flow instance referenced by link",
            Severity.ERROR,
            msg,
        )


class MissingNodeInstance(ProjIssue):
    """Missing node instance referenced by link.

    Attributes:
        json_path (Path): Path to file with issue.
        msg (str): Issue message.

    """

    def __init__(
        self,
        json_path: Path,
        msg: str,
    ) -> None:
        self.json_path = json_path

        super().__init__(
            "Formating",
            "Missing node instance referenced by link",
            Severity.ERROR,
            msg,
        )


class DuplicatedMob(ProjIssue):
    """Duplicated MOV.AI object is detected

    Attributes:
        msg (str): Issue message.

    """

    def __init__(
        self,
        msg: str,
    ) -> None:
        super().__init__(
            "Formating",
            "Duplicated metadata",
            Severity.ERROR,
            msg,
        )


class MissingMob(ProjIssue):
    """Missing mob (node or flow).

    Attributes:
        json_path (Path): Path to file with issue.
        msg (str): Issue message.

    """

    def __init__(
        self,
        json_path: Path,
        msg: str,
    ) -> None:
        self.json_path = json_path

        super().__init__(
            "Formating",
            "Missing Flow or Node",
            Severity.ERROR,
            msg,
        )


class MissingNodePort(ProjIssue):
    """Missing node port.

    Attributes:
        json_path (Path): Path to file with issue.
        msg (str): Issue message.

    """

    def __init__(
        self,
        json_path: Path,
        msg: str,
    ) -> None:
        self.json_path = json_path

        super().__init__(
            "Formating",
            "Missing Node port",
            Severity.ERROR,
            msg,
        )


class NonMatchingLinkPorts(ProjIssue):
    """Link src and dst ports do not match (should not be connected).

    Attributes:
        json_path (Path): Path to file with issue.
        msg (str): Issue message.

    """

    def __init__(
        self,
        json_path: Path,
        msg: str,
    ) -> None:
        self.json_path = json_path

        super().__init__(
            "Formating",
            "Non matching link ports",
            Severity.ERROR,
            msg,
        )
