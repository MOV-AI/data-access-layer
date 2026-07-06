from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional


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
        line_start: Optional[int] = None,
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
        line_start: Optional[int] = None,
    ) -> None:
        self.json_path = json_path

        super().__init__(
            "Formating",
            "Missing flow instance referenced by link",
            Severity.ERROR,
            msg,
            line_start=line_start,
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
        line_start: Optional[int] = None,
    ) -> None:
        self.json_path = json_path

        super().__init__(
            "Formating",
            "Missing node instance referenced by link",
            Severity.ERROR,
            msg,
            line_start=line_start,
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
        line_start: Optional[int] = None,
    ) -> None:
        self.json_path = json_path

        super().__init__(
            "Formating",
            "Missing Flow or Node",
            Severity.ERROR,
            msg,
            line_start=line_start,
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
        line_start: Optional[int] = None,
    ) -> None:
        self.json_path = json_path

        super().__init__(
            "Formating",
            "Missing Node port",
            Severity.ERROR,
            msg,
            line_start=line_start,
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
        line_start: Optional[int] = None,
    ) -> None:
        self.json_path = json_path

        super().__init__(
            "Formating",
            "Non matching link ports",
            Severity.ERROR,
            msg,
            line_start=line_start,
        )
