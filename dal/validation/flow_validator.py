from movai_core_shared import Log
from movai_core_shared.exceptions import DoesNotExist
from dal.scopes.flow import Flow
from dal.validation.issues import Severity
from dal.validation.project_validator import (
    ProjectIssue,
    ProjectValidator,
    Summary,
    ProjectValidationResult,
)

LOGGER = Log.get_logger(__name__)


class FlowValidator:
    """
    Validates a specific flow within the project.
    """

    def __init__(self, flow_ref: str):
        try:
            self.flow = Flow(flow_ref)
        except Exception as e:
            LOGGER.error(f"Error initializing FlowValidator for flow {flow_ref}: {e}")
            raise DoesNotExist(f"Error initializing FlowValidator for flow {flow_ref}: {e}")

        self.project = ProjectValidator()
        self.flow_ref = flow_ref
        self.issues = []

    def validate_flow(self) -> ProjectValidationResult:
        """
        Validate a specific flow by its reference.

        Returns:
            ProjectValidationResult: The result of the flow validation, including issues found.
        """
        try:
            # Validate the specific flow
            self.issues.extend(self.project.check_flow(self.flow_ref))

        except Exception as e:
            LOGGER.error(f"Error validating flow {self.flow_ref}: {e}")
            raise

        return ProjectValidationResult(
            summary=Summary(
                total_issues=len(self.issues),
                error_count=sum(1 for issue in self.issues if issue.severity == Severity.ERROR),
                warning_count=sum(1 for issue in self.issues if issue.severity != Severity.ERROR),
                scopes_checked=["Flow"],
            ),
            issues=[
                ProjectIssue(
                    category=issue.category,
                    iss_type=issue.iss_type,
                    severity=issue.severity,
                    msg=issue.msg,
                    json_path=getattr(issue, "json_path", "N/A"),
                    document_type=getattr(issue, "document_type", "Flow"),
                    document_name=getattr(issue, "document_name", self.flow_ref),
                    line_start=getattr(issue, "line_start", None),
                )
                for issue in self.issues
            ],
        )
