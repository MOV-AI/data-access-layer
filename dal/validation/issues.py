from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional


class Severity(str, Enum):
    """Severity enumeration."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    ERROR = "ERROR"

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

    def __init__(
        self,
        category: str,
        iss_type: str,
        severity: Severity,
        msg: str,
        json_path: Path,
        line_start: Optional[int] = None,
        line_ranges: List[Dict[str, int]] = None,
        document_type: str = "Unknown",
        document_name: str = "Unknown",
    ) -> None:
        self.json_path = json_path
        self.document_type = document_type
        self.document_name = document_name
        super().__init__(
            category=category,
            iss_type=iss_type,
            severity=severity,
            msg=msg,
            line_start=line_start,
            line_ranges=line_ranges,
        )

    def __str__(self) -> str:
        """Provides issue string representation.

        Returns:
            The issue string representation.

        """

        level = str(self.severity) if self.severity == Severity.ERROR else "Warn"

        return f"[{level}] {self.msg}"


class DuplicatedMob(ProjIssue):
    """Duplicated flow or node instance in multiple packages

    Attributes:
        msg (str): Issue message.

    """

    def __init__(
        self,
        json_path: Path,
        msg: str,
        document_type: str = "Unknown",
        document_name: str = "Unknown",
    ) -> None:
        super().__init__(
            category="Formating",
            iss_type="Duplicated metadata",
            severity=Severity.ERROR,
            msg=msg,
            json_path=json_path,
            document_type=document_type,
            document_name=document_name,
        )


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
        document_type: str = "Unknown",
        document_name: str = "Unknown",
    ) -> None:
        super().__init__(
            category="Formating",
            iss_type="Missing flow instance referenced by link",
            severity=Severity.ERROR,
            msg=msg,
            json_path=json_path,
            line_start=line_start,
            document_type=document_type,
            document_name=document_name,
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
        document_type: str = "Unknown",
        document_name: str = "Unknown",
    ) -> None:
        super().__init__(
            category="Formating",
            iss_type="Missing node instance referenced by link",
            severity=Severity.ERROR,
            msg=msg,
            json_path=json_path,
            line_start=line_start,
            document_type=document_type,
            document_name=document_name,
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
        document_type: str = "Unknown",
        document_name: str = "Unknown",
    ) -> None:
        super().__init__(
            category="Formating",
            iss_type="Missing Flow or Node",
            severity=Severity.ERROR,
            msg=msg,
            json_path=json_path,
            line_start=line_start,
            document_type=document_type,
            document_name=document_name,
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
        document_type: str = "Unknown",
        document_name: str = "Unknown",
    ) -> None:
        super().__init__(
            category="Formating",
            iss_type="Missing Node port",
            severity=Severity.ERROR,
            msg=msg,
            json_path=json_path,
            line_start=line_start,
            document_type=document_type,
            document_name=document_name,
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
        document_type: str = "Unknown",
        document_name: str = "Unknown",
    ) -> None:
        super().__init__(
            category="Formating",
            iss_type="Non matching link ports",
            severity=Severity.ERROR,
            msg=msg,
            json_path=json_path,
            line_start=line_start,
            document_type=document_type,
            document_name=document_name,
        )


class MissingReferencedParameter(ProjIssue):
    """Missing flow parameter referenced by node instance.

    Attributes:
        json_path (Path): Path to file with issue.
        msg (str): Issue message.

    """

    def __init__(
        self,
        json_path: Path,
        msg: str,
        line_start: Optional[int] = None,
        document_type: str = "Unknown",
        document_name: str = "Unknown",
    ) -> None:
        super().__init__(
            category="Formating",
            iss_type="Missing referenced parameter",
            severity=Severity.ERROR,
            msg=msg,
            json_path=json_path,
            line_start=line_start,
            document_type=document_type,
            document_name=document_name,
        )
