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

    @staticmethod
    def _join_flow_path(parent_path: str, container_name: str) -> str:
        """Join a parent container path and child container name."""

        return f"{parent_path}__{container_name}" if parent_path else container_name

    def _collect_flow_contexts(self, flow_ref: str, flow_path: str = "", ancestors=None):
        """
        Collect a flow and all subflows referenced by its containers with their mount paths.
        """

        ancestors = ancestors or set()
        if flow_ref in ancestors:
            return []

        ancestors.add(flow_ref)
        flow_contexts = [(flow_ref, flow_path)]

        try:
            flow_data = self.project._get_flow_dict(flow_ref)
        except Exception as e:
            LOGGER.error(f"Error loading flow {flow_ref}: {e}")
            return flow_contexts

        flow_content = flow_data.get("Flow", {}).get(flow_ref, {})
        for container_name, container_data in flow_content.get("Container", {}).items():
            subflow_ref = container_data.get("ContainerFlow")
            if not subflow_ref or subflow_ref in ancestors:
                continue

            if not self.project._object_exists("Flow", subflow_ref):
                continue

            flow_contexts.extend(
                self._collect_flow_contexts(
                    subflow_ref,
                    self._join_flow_path(flow_path, container_name),
                    set(ancestors),
                )
            )

        return flow_contexts

    def validate_flow(self) -> ProjectValidationResult:
        """
        Validate a specific flow and all subflows reachable from it.

        Returns:
            ProjectValidationResult: The result of the flow validation, including issues found.
        """
        try:
            self.issues = []

            from dal.helpers.parsers import ParamParser

            with ParamParser.dedupe_validation_disabled_warnings():
                for flow_ref, flow_path in self._collect_flow_contexts(self.flow_ref):
                    self.issues.extend(
                        self.project.check_flow(
                            flow_ref,
                            context=self.flow_ref,
                            node_prefix=flow_path,
                        )
                    )

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
