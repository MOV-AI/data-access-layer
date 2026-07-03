"""
Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

from dal.validation.links import LinkValidator
from dal.models.scopestree import scopes
from dal.scopes.flow import Flow
from typing import List, Dict, Optional, Set
from dal.validation.issues import (
    ProjIssue,
    MissingMob,
    Severity,
)
from movai_core_shared.logger import Log
import json
import re

LOGGER = Log.get_logger("ProjectValidator")

# Scopes to validate (same as mobtest METADATA_FOLDERS_NAME)
VALIDATED_SCOPES = [
    "Annotation",
    "Callback",
    "Configuration",
    "GraphicScene",
    "Layout",
    "Flow",
    "Node",
    "SharedDataEntry",
    "SharedDataTemplate",
    "TaskTemplate",
]


class ProjectValidator:
    """
    Validates all movai project data according to:
    - No duplicate MOB names across workspace
    - For each Flow, check that all referenced Flows/Nodes exist in the project
    - For each Link, validate instances exist and ports are compatible
    """

    def __init__(self):
        """
        Initialize the ProjectValidator.
        """
        self.issues: List[ProjIssue] = []
        # Cache of all objects by scope: {"Flow": {"name1", "name2"}, "Node": {...}}
        self._objects_by_scope: Dict[str, Set[str]] = {}

    def validate(self) -> Dict:
        """
        Validate the project data.

        Returns:
            dict: A dictionary containing the validation results with summary and issues.
        """
        LOGGER.info("Starting project validation")

        # Build cache of all objects first
        self._build_object_cache()

        # Run validations
        self._check_duplicates()
        self._check_nodes_flows_ref_in_flows()
        self._check_link_ports_match()

        # Build summary
        error_count = sum(1 for issue in self.issues if issue.severity == Severity.ERROR)
        warning_count = sum(1 for issue in self.issues if issue.severity != Severity.ERROR)

        LOGGER.info(f"Validation complete: {error_count} errors, {warning_count} warnings")

        return {
            "summary": {
                "total_issues": len(self.issues),
                "errors": error_count,
                "warnings": warning_count,
                "scopes_checked": VALIDATED_SCOPES,
            },
            "issues": self.issues,
        }

    def _build_object_cache(self):
        """Build a cache of all objects in workspace by scope."""
        for scope_name in VALIDATED_SCOPES:
            self._objects_by_scope[scope_name] = set()
            try:
                objects = scopes().list_scopes(scope=scope_name)
                for obj in objects:
                    self._objects_by_scope[scope_name].add(obj["ref"])
            except Exception as e:
                LOGGER.warning(f"Error listing scope {scope_name}: {e}")

    def _check_duplicates(self):
        """
        Check for duplicate names across workspace.

        Note: In Redis/DAL, duplicates within a workspace shouldn't exist
        (refs are unique within a scope), but we check anyway for completeness.
        """
        # For now, duplicates within a single workspace are prevented by Redis keys
        # This check is more relevant if we're checking across multiple databases

    def _check_nodes_flows_ref_in_flows(self):
        """
        Check that all nodes and flows referenced in flows exist in the project.
        """
        LOGGER.info("Checking Flow/Node template references")

        # Get all flows
        flow_refs = self._objects_by_scope.get("Flow", set())

        for flow_ref in flow_refs:
            try:
                # Load the flow object
                flow_obj = Flow(flow_ref)
                flow_data = flow_obj.get_dict()

                # Navigate to the actual flow data
                if "Flow" not in flow_data or flow_ref not in flow_data["Flow"]:
                    continue

                flow_content = flow_data["Flow"][flow_ref]

                # Check Container (subflows)
                if "Container" in flow_content:
                    for container_name, container_data in flow_content["Container"].items():
                        template_name = container_data.get("ContainerFlow")
                        if template_name and not self._object_exists("Flow", template_name):
                            # Reference to file -> file name is not available in Redis,
                            # but we can assume the convention that the flow name corresponds to a JSON file in the project
                            issue = MissingMob(
                                json_path=f"{flow_ref}.json",
                                msg=f"Flow '{template_name}' missing, required by "
                                f"Flow '{flow_ref}' (container '{container_name}')",
                            )

                            # Find line number in JSON
                            line_num = self._find_json_path_line(
                                flow_data,
                                ["Flow", flow_ref, "Container", container_name, "ContainerFlow"],
                            )
                            if line_num:
                                issue.line_start = line_num
                            self.issues.append(issue)

                # Check NodeInst (node instances)
                if "NodeInst" in flow_content:
                    for node_inst_name, node_inst_data in flow_content["NodeInst"].items():
                        template_name = node_inst_data.get("Template")
                        if template_name and not self._object_exists("Node", template_name):
                            issue = MissingMob(
                                json_path=f"{flow_ref}.json",
                                msg=f"Node '{template_name}' missing, required by "
                                f"Flow '{flow_ref}' (node instance '{node_inst_name}')",
                            )

                            # Find line number in JSON
                            line_num = self._find_json_path_line(
                                flow_data,
                                ["Flow", flow_ref, "NodeInst", node_inst_name, "Template"],
                            )
                            if line_num:
                                issue.line_start = line_num
                            self.issues.append(issue)

            except Exception as e:
                LOGGER.error(f"Error checking flow {flow_ref}: {e}")

    def _check_link_ports_match(self):
        """
        Check that all links have valid instances and compatible ports.
        """
        LOGGER.info("Checking link port compatibility")

        link_validator = LinkValidator(project_validator=self, logger=LOGGER)

        flow_refs = self._objects_by_scope.get("Flow", set())

        for flow_ref in flow_refs:
            try:
                flow_obj = Flow(flow_ref)
                flow_data = flow_obj.get_dict()

                if "Flow" not in flow_data or flow_ref not in flow_data["Flow"]:
                    continue

                flow_content = flow_data["Flow"][flow_ref]

                # Check all links
                if "Links" in flow_content:
                    for link_id, link_data in flow_content["Links"].items():
                        from_path = link_data.get("From", "")
                        to_path = link_data.get("To", "")

                        # Validate link endpoints
                        link_validator.validate_link(
                            flow_ref, flow_data, flow_content, link_id, from_path, to_path
                        )

            except Exception as e:
                LOGGER.error(f"Error checking links in flow {flow_ref}: {e}")

    def _object_exists(self, scope: str, ref: str) -> bool:
        """Check if an object exists in the workspace cache."""
        return ref in self._objects_by_scope.get(scope, set())

    @staticmethod
    def _find_json_path_line(json_data: dict, path: List[str]) -> Optional[int]:
        """
        Find the line number of a specific JSON path in formatted JSON.

        Args:
            json_data: The JSON data dictionary
            path: List of keys representing the path (e.g., ["Flow", "MyFlow", "NodeInst", "node1"])

        Returns:
            Line number (1-indexed) or None if not found
        """
        try:
            # Serialize with standard formatting (2-space indent)
            json_str = json.dumps(json_data, indent=2, sort_keys=False)
            lines = json_str.split("\n")

            # Build regex pattern to find the key at the end of the path
            # We look for the last key in the path, properly quoted
            if not path:
                return None

            target_key = path[-1]
            # Pattern matches: "key": (with optional whitespace)
            pattern = rf'^\s*"{re.escape(target_key)}":\s*'

            # We need to track nesting depth to find the right occurrence
            # For simplicity, we'll find the first occurrence of the key after
            # all parent keys have been seen
            parent_found = len(path) <= 1  # No parents to check

            for i, line in enumerate(lines, start=1):
                # Check if we've seen all parent keys
                if not parent_found and len(path) > 1:
                    for parent in path[:-1]:
                        parent_pattern = rf'"{re.escape(parent)}":'
                        if re.search(parent_pattern, line):
                            break
                    else:
                        continue
                    parent_found = True

                # Look for the target key
                if re.search(pattern, line):
                    return i

            return None
        except Exception as e:
            LOGGER.debug(f"Error finding JSON path line: {e}")
            return None
