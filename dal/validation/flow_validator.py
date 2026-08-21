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

    def _collect_flow_refs(self, flow_ref: str, visited=None):
        """
        Collect a flow and all subflows referenced by its containers.
        """

        visited = visited or set()
        if flow_ref in visited:
            return []

        visited.add(flow_ref)
        flow_refs = [flow_ref]

        try:
            flow_data = self.project._get_flow_dict(flow_ref)
        except Exception as e:
            LOGGER.error(f"Error loading flow {flow_ref}: {e}")
            return flow_refs

        flow_content = flow_data.get("Flow", {}).get(flow_ref, {})
        for container_data in flow_content.get("Container", {}).values():
            subflow_ref = container_data.get("ContainerFlow")
            if not subflow_ref or subflow_ref in visited:
                continue

            if not self.project._object_exists("Flow", subflow_ref):
                continue

            flow_refs.extend(self._collect_flow_refs(subflow_ref, visited))

        return flow_refs

    def validate_flow(self) -> ProjectValidationResult:
        """
        Validate a specific flow and all subflows reachable from it.

        Returns:
            ProjectValidationResult: The result of the flow validation, including issues found.
        """
        try:
            self.issues = []
            for flow_ref in self._collect_flow_refs(self.flow_ref):
                self.issues.extend(self.project.check_flow(flow_ref))

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
