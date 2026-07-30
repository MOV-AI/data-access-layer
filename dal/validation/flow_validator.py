from typing import List

from movai_core_shared import Log
from dal.validation.issues import ProjIssue, Severity
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
        self.project = ProjectValidator()
        self.flow_ref = flow_ref
        self.issues = []

    def validate_flow(self) -> List[ProjIssue]:
        """
        Validate a specific flow by its reference.

        Returns:
            List[ProjIssue]: A list of issues found for this specific flow.
        """
        try:
            # Build object cache if not already built
            if not self.project._objects_by_scope:
                self.project._build_object_cache()

            # Validate the specific flow
            self.issues.extend(self.project._check_nodes_flows_ref_in_flow(self.flow_ref))
            self.issues.extend(self.project._check_flow_parameters(self.flow_ref))
            self.issues.extend(self.project._check_flow_links(self.flow_ref))

        except Exception as e:
            LOGGER.error(f"Error validating flow {self.flow_ref}: {e}")

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
                    line_start=getattr(issue, "line_start", None),
                )
                for issue in self.issues
            ],
        )
