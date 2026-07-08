"""
Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

from dal.models.scopestree import scopes
from dal.models.package import Package
from dal.scopes.flow import Flow, Node
from typing import List, Dict, Optional, Set
from pydantic import BaseModel, ConfigDict
from dal.validation.issues import (
    ProjIssue,
    DuplicatedMob,
    MissingMob,
    Severity,
    NonMatchingLinkPorts,
    MissingFlowInstance,
    MissingNodeInstance,
    MissingNodePort,
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


class Summary(BaseModel):
    """Summary of validation results."""

    total_issues: int
    errors: int
    warnings: int
    scopes_checked: List[str]


class ProjectIssue(BaseModel):
    """Base class for project validation issues."""

    category: str
    iss_type: str
    severity: Severity
    msg: str
    json_path: str
    line_start: Optional[int] = None

    def __str__(self):
        return f"[{self.severity.name}] {self.category} - {self.iss_type}: {self.msg} (Line: {self.line_start})"


class ProjectValidationResult(BaseModel):
    """Result structure for usage search.

    Format:
    {
        "summary": {
            "total_issues": int,
            "errors": int,
            "warnings": int,
            "scopes_checked": List[str]
        },
        "issues": List[ProjectIssue]
    }
    """

    # To allow for ProjIssue instances in the issues list
    model_config = ConfigDict(arbitrary_types_allowed=True)

    summary: Summary
    issues: List[ProjectIssue]


class MissingFlowTemplateExc(Exception):
    """Raised when a flow template is not found."""


class MissingNodeTemplateExc(Exception):
    """Raised when a node template is not found."""


class MissingFlowInstanceExc(Exception):
    """Raised when a flow instance is not found.

    Attributes:
        flow (str): Flow where the instance is missing.
        expected_instance (str): Instance missing.

    """

    def __init__(self, flow: str, expected_instance: str):
        self.flow = flow
        self.expected_instance = expected_instance


class MissingNodeInstanceExc(Exception):
    """Raised when a node instance is not found.

    Attributes:
        flow (str): Flow where the instance is missing.
        expected_instance (str): Instance missing.

    """

    def __init__(self, flow: str, expected_instance: str):
        self.flow = flow
        self.expected_instance = expected_instance


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

        return ProjectValidationResult(
            summary=Summary(
                total_issues=len(self.issues),
                errors=error_count,
                warnings=warning_count,
                scopes_checked=VALIDATED_SCOPES,
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

        In Redis/DAL, duplicates within a workspace shouldn't exist
        We check for duplicates in the packages information stored in the local db
        """
        LOGGER.info("Checking for duplicate names across workspace")

        # Get all objects from the package data
        all_packages_sys = Package.get_packagedata()
        all_packages = all_packages_sys.Value if isinstance(all_packages_sys.Value, dict) else {}

        # Check for duplicates per workspace
        for workspace_name, packages_dict in all_packages.items():
            # Track objects by scope and name to find duplicates
            # Structure: {scope: {object_name: [package1, package2, ...]}}
            objects_by_scope_and_name: Dict[str, Dict[str, List[str]]] = {}

            for package_name, package_entry in packages_dict.items():
                # Extract scope lists from "data" sub-dict
                scopes_dict = package_entry.get("data", {})
                for scope, objects_list in scopes_dict.items():
                    if not isinstance(objects_list, list):
                        continue
                    if scope not in objects_by_scope_and_name:
                        objects_by_scope_and_name[scope] = {}

                    for obj_name in objects_list:
                        if obj_name not in objects_by_scope_and_name[scope]:
                            objects_by_scope_and_name[scope][obj_name] = []
                        objects_by_scope_and_name[scope][obj_name].append(package_name)

            # Check for duplicates within each scope
            for scope, objects_dict in objects_by_scope_and_name.items():
                for obj_name, packages_list in objects_dict.items():
                    if len(packages_list) > 1:
                        issue = DuplicatedMob(
                            json_path=f"{obj_name}.json",
                            msg=f"Duplicate MOB name '{obj_name}' found in packages: {', '.join(sorted(packages_list))} installed in workspace '{workspace_name}'",
                        )
                        self.issues.append(issue)

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
                            line_num = _find_json_path_line(
                                flow_data,
                                ["Flow", flow_ref, "Container", container_name, "ContainerFlow"],
                            )
                            # Reference to file -> file name is not available in Redis,
                            # but we can assume the convention that the flow name corresponds to a JSON file in the project
                            issue = MissingMob(
                                json_path=f"{flow_ref}.json",
                                msg=f"Flow '{template_name}' missing, required by Flow '{flow_ref}' (instance '{container_name}')",
                                line_start=line_num,
                            )
                            self.issues.append(issue)

                # Check NodeInst (node instances)
                if "NodeInst" in flow_content:
                    for node_inst_name, node_inst_data in flow_content["NodeInst"].items():
                        template_name = node_inst_data.get("Template")
                        if template_name and not self._object_exists("Node", template_name):
                            line_num = _find_json_path_line(
                                flow_data,
                                ["Flow", flow_ref, "NodeInst", node_inst_name, "Template"],
                            )
                            issue = MissingMob(
                                json_path=f"{flow_ref}.json",
                                msg=f"Node '{template_name}' missing, required by Flow '{flow_ref}' (instance '{node_inst_name}')",
                                line_start=line_num,
                            )
                            self.issues.append(issue)

            except Exception as e:
                LOGGER.error(f"Error checking flow {flow_ref}: {e}")

    def _check_link_ports_match(self):
        """
        Check that all links have valid instances and compatible ports.
        """
        LOGGER.info("Checking link port compatibility")

        link_validator = LinkValidator(objects_by_scope=self._objects_by_scope, logger=LOGGER)

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
                        self.issues.extend(
                            link_validator.validate_link(
                                flow_ref, flow_data, flow_content, link_id, from_path, to_path
                            )
                        )

            except Exception as e:
                LOGGER.error(f"Error checking links in flow {flow_ref}: {e}")

    def _object_exists(self, scope: str, ref: str) -> bool:
        """Check if an object exists in the workspace cache."""
        return ref in self._objects_by_scope.get(scope, set())


class LinkValidator:
    """Link validator class."""

    def __init__(self, objects_by_scope: Dict, logger):
        self._objects_by_scope = objects_by_scope
        self.logger = logger

    def validate_link(
        self,
        flow_ref: str,
        flow_data: dict,
        flow_content: dict,
        link_id: str,
        from_path: str,
        to_path: str,
    ) -> List[ProjIssue]:
        """
        Validate a single link.

        Args:
            flow_ref: Name of the flow containing the link
            flow_data: Full flow data dictionary (for line number lookup)
            flow_content: Flow content dictionary
            link_id: Link identifier
            from_path: Link source path (format: "node__subnode/port/out")
            to_path: Link destination path (format: "node__subnode/port/in")
        """
        issues = []

        # Parse link paths
        from_info = self._parse_link_path(
            flow_ref, flow_data, flow_content, from_path, "from", link_id
        )
        to_info = self._parse_link_path(flow_ref, flow_data, flow_content, to_path, "to", link_id)

        # Check if parsing succeeded
        if from_info.get("error"):
            issues.append(from_info["error"])
            return issues
        if to_info.get("error"):
            issues.append(to_info["error"])
            return issues

        # Keep mobtest parity: if a node/flow template is missing in a link path,
        # skip link checks here because template-reference validation already reports it.
        if from_info.get("template_missing") or to_info.get("template_missing"):
            return []

        # Check if ports exist on the node templates
        src_port_type = from_info.get("port_type")
        dst_port_type = to_info.get("port_type")

        # Check source port existence (mobtest parity: return early like 'continue')
        if not src_port_type:
            line_num = _find_json_path_line(flow_data, ["Flow", flow_ref, "Links", link_id, "From"])
            issue = MissingNodePort(
                json_path=f"{flow_ref}.json",
                msg=f"Source port of link {link_id} does not exist | From: {from_path} | To: {to_path}",
                line_start=line_num,
            )
            issues.append(issue)
            return issues

        # Check destination port existence (mobtest parity: return early like 'continue')
        if not dst_port_type:
            line_num = _find_json_path_line(flow_data, ["Flow", flow_ref, "Links", link_id, "To"])
            issue = MissingNodePort(
                json_path=f"{flow_ref}.json",
                msg=f"Destination port of link {link_id} does not exist | From: {from_path} | To: {to_path}",
                line_start=line_num,
            )
            issues.append(issue)
            return issues

        # Check port compatibility
        if not self._ports_match(src_port_type, dst_port_type):
            line_num = _find_json_path_line(flow_data, ["Flow", flow_ref, "Links", link_id])
            issue = NonMatchingLinkPorts(
                json_path=f"{flow_ref}.json",
                msg=f"The ports of link {link_id} in Flow {flow_ref} do not match | From: {from_path} | To: {to_path}",
                line_start=line_num,
            )
            issues.append(issue)

        return issues

    def _parse_link_path(
        self,
        flow_ref: str,
        flow_data: dict,
        flow_content: dict,
        path: str,
        direction: str,
        link_id: str = None,
    ) -> dict:
        """
        Parse and validate a link path.

        Args:
            flow_ref: Flow name
            flow_data: Full flow data (for line number lookup)
            flow_content: Flow content dictionary
            path: Link path (e.g., "node_inst/port_name/in")
            direction: "from" or "to"
            link_id: Link identifier (for line number reporting)

        Returns:
            dict with parsing results and potential error
        """
        if path == "start/start/start":
            # Special start node, always valid - returns TransitionFor port type
            return {
                "valid": True,
                "instance": "start",
                "port": "start",
                "port_type": {
                    "Message": "Transition",
                    "Out": {"out": {"Message": "movai_msgs/Transition"}},
                    "Package": "movai_msgs",
                    "Template": "MovAI/TransitionFor",
                },
                "template": "start",
            }

        try:
            # Split path: node__subnode/port/direction
            parts = path.split("/")
            if len(parts) < 3:
                return {"valid": False}

            instances = parts[0].split("__")  # Can be nested: subflow__node
            port_name = "/".join(parts[1:-1])  # Port name can contain /
            port_direction = parts[-1]

            # Start with current flow
            current_flow_data = flow_content

            # Navigate through subflows (all but last instance)
            for i, instance in enumerate(instances[:-1]):
                # This should be a Container (subflow)
                if "Container" not in current_flow_data:
                    # Find line number for the link
                    line_num = (
                        _find_json_path_line(
                            flow_data, ["Flow", flow_ref, "Links", link_id, direction.capitalize()]
                        )
                        if link_id
                        else None
                    )

                    issue = MissingFlowInstance(
                        json_path=f"{flow_ref}.json",
                        msg=f"Link {link_id} path references missing flow instance '{instance}' in Flow '{flow_ref}'",
                        line_start=line_num,
                    )
                    return {"valid": False, "error": issue}

                if instance not in current_flow_data["Container"]:
                    line_num = (
                        _find_json_path_line(
                            flow_data, ["Flow", flow_ref, "Links", link_id, direction.capitalize()]
                        )
                        if link_id
                        else None
                    )
                    issue = MissingFlowInstance(
                        json_path=f"{flow_ref}.json",
                        msg=f"Flow instance '{instance}' not found in Flow '{flow_ref}' (referenced in link {link_id} path)",
                        line_start=line_num,
                    )
                    return {"valid": False, "error": issue}

                # Get flow template and move to that flow data (mobtest parity)
                template_name = current_flow_data["Container"][instance].get("ContainerFlow")
                if not template_name or not self._object_exists("Flow", template_name):
                    raise MissingFlowTemplateExc(template_name)

                template_flow = Flow(template_name)
                template_flow_data = template_flow.get_dict()
                if (
                    "Flow" not in template_flow_data
                    or template_name not in template_flow_data["Flow"]
                ):
                    raise MissingFlowTemplateExc(template_name)

                current_flow_data = template_flow_data["Flow"][template_name]

            # Last instance should be a NodeInst
            final_instance = instances[-1]
            if "NodeInst" not in current_flow_data:
                line_num = (
                    _find_json_path_line(
                        flow_data, ["Flow", flow_ref, "Links", link_id, direction.capitalize()]
                    )
                    if link_id
                    else None
                )
                issue = MissingNodeInstance(
                    json_path=f"{flow_ref}.json",
                    msg=f"Link {link_id} path references missing node instance '{final_instance}' in Flow '{flow_ref}'",
                    line_start=line_num,
                )
                return {"valid": False, "error": issue}

            if final_instance not in current_flow_data["NodeInst"]:
                line_num = (
                    _find_json_path_line(
                        flow_data, ["Flow", flow_ref, "Links", link_id, direction.capitalize()]
                    )
                    if link_id
                    else None
                )
                issue = MissingNodeInstance(
                    json_path=f"{flow_ref}.json",
                    msg=f"Node instance '{final_instance}' not found in Flow '{flow_ref}' (referenced in link {link_id} path)",
                    line_start=line_num,
                )
                return {"valid": False, "error": issue}

            # Get the node template name and load port information
            node_inst_data = current_flow_data["NodeInst"][final_instance]
            template_name = node_inst_data.get("Template")

            # Get port type from the node template
            port_type = self._get_port_type(template_name, port_name) if template_name else {}

            return {
                "valid": True,
                "instance": final_instance,
                "port": port_name,
                "port_type": port_type,
                "template": template_name,
            }

        except (MissingNodeTemplateExc, MissingFlowTemplateExc):
            return {"valid": False, "template_missing": True}
        except Exception as e:
            self.logger.warning(f"Error parsing link path {path}: {e}")
            return {"valid": False}

    def _get_port_type(self, node_template: str, port_name: str) -> dict:
        """
        Get port type information from a Node template.
        Equivalent to mobtest: template_node.dict_data["Node"][template_name]["PortsInst"][port_name]

        Args:
            node_template: Name of the Node template
            port_name: Name of the port

        Returns:
            Port type dictionary or empty dict if port not found
        """
        if node_template and not self._object_exists("Node", node_template):
            raise MissingNodeTemplateExc(node_template)

        try:
            node = Node(node_template)
            node_data = node.get_dict()

            # Direct access equivalent to mobtest's template_node.dict_data["Node"][template_name]["PortsInst"]
            if "Node" in node_data and node_template in node_data["Node"]:
                node_content = node_data["Node"][node_template]
                ports_inst = node_content.get("PortsInst", {})
                return ports_inst.get(port_name, {})

            return {}
        except MissingNodeTemplateExc:
            raise
        except Exception as e:
            self.logger.debug(f"Error getting port type for {node_template}/{port_name}: {e}")
            return {}

    def _ports_match(self, src_port: dict, dst_port: dict) -> bool:
        """
        Check if source and destination ports are compatible.
        Based on mobtest Link.ports_match() logic.

        Args:
            src_port: Source port type dictionary
            dst_port: Destination port type dictionary

        Returns:
            True if ports are compatible, False otherwise
        """
        try:
            # Get port attributes safely
            src_pkg = src_port.get("Package", "")
            src_msg = src_port.get("Message", "")
            src_template = src_port.get("Template", "")
            src_out = src_port.get("Out", {}).get("out", {}).get("Message", "")

            dst_pkg = dst_port.get("Package", "")
            dst_msg = dst_port.get("Message", "")
            dst_template = dst_port.get("Template", "")
            dst_in = dst_port.get("In", {}).get("in", {}).get("Message", "")

            # Source: movai_msgs/Any (can connect to anything except transitions)
            if (
                src_pkg == "movai_msgs"
                and src_msg == "Any"
                and src_template == "ROS1/Publisher"
                and src_out == "movai_msgs/Any"
                and not (
                    dst_pkg == "movai_msgs"
                    and dst_msg == "Transition"
                    and dst_template == "MovAI/TransitionTo"
                    and dst_in == "movai_msgs/Transition"
                )
            ):
                return True

            # Destination: movai_msgs/Any (can receive from anything except transitions)
            if (
                dst_pkg == "movai_msgs"
                and dst_msg == "Any"
                and dst_template == "ROS1/Subscriber"
                and dst_in == "movai_msgs/Any"
                and not (
                    src_pkg == "movai_msgs"
                    and src_msg == "Transition"
                    and src_template == "MovAI/TransitionFor"
                    and src_out == "movai_msgs/Transition"
                )
            ):
                return True

            # MovAI internal packages
            if src_pkg == dst_pkg == "movai_msgs":
                # Dependency
                if (
                    src_msg == dst_msg == "Dependency"
                    and src_template == "MovAI/Depends"
                    and dst_template == "MovAI/Dependency"
                    and src_out == dst_in == "movai_msgs/Dependency"
                ):
                    return True

                # Transition
                if (
                    src_msg == dst_msg == "Transition"
                    and src_template == "MovAI/TransitionFor"
                    and dst_template == "MovAI/TransitionTo"
                    and src_out == dst_in == "movai_msgs/Transition"
                ):
                    return True

                # ROS1 Nodelet
                if (
                    src_msg == dst_msg == "Nodelet"
                    and src_template == "ROS1/NodeletClient"
                    and dst_template == "ROS1/NodeletServer"
                    and src_out == dst_in == "movai_msgs/Nodelet"
                ):
                    return True

                # ROS1 Plugin
                if (
                    src_msg == dst_msg == "Plugin"
                    and src_template == "ROS1/PluginClient"
                    and dst_template == "ROS1/PluginServer"
                    and src_out == dst_in == "movai_msgs/Plugin"
                ):
                    return True

                # ROS1 Reconfigure
                if (
                    src_msg == dst_msg == "Reconfigure"
                    and src_template == "ROS1/ReconfigureClient"
                    and dst_template == "ROS1/ReconfigureServer"
                    and src_out == dst_in == "movai_msgs/Reconfigure"
                ):
                    return True

            # Package match
            if src_pkg == dst_pkg:
                # Message match
                if src_msg == dst_msg:
                    # ROS1 pub/sub
                    if src_template == "ROS1/Publisher" and dst_template == "ROS1/Subscriber":
                        return True

                    # ROS1 service
                    if (
                        src_template == "ROS1/ServiceClient"
                        and dst_template == "ROS1/ServiceServer"
                        and src_out == dst_in
                    ):
                        return True

                    # ROS1 action (bidirectional)
                    if (
                        src_template == "ROS1/ActionClient" and dst_template == "ROS1/ActionServer"
                    ) or (
                        src_template == "ROS1/ActionServer" and dst_template == "ROS1/ActionClient"
                    ):
                        return True

            # ROS1 pub/topichz
            if (
                src_template == "ROS1/Publisher"
                and dst_template == "ROS1/TopicHz"
                and dst_msg == "Any"
                and dst_pkg == "movai_msgs"
            ):
                return True

            return False

        except Exception as e:
            self.logger.debug(f"Error checking port compatibility: {e}")
            return True

    def _object_exists(self, scope: str, ref: str) -> bool:
        """Check if an object exists in the workspace cache."""
        return ref in self._objects_by_scope.get(scope, set())


def _find_json_path_line(json_data: dict, path: List[str]) -> Optional[int]:
    """
    Find the line number of a specific JSON path in formatted JSON.

    Uses MOV.AI standard formatting (indent=4, sort_keys=True) to match
    how files are exported from Redis and displayed in the IDE.

    Args:
        json_data: The JSON data dictionary
        path: List of keys representing the path (e.g., ["Flow", "MyFlow", "NodeInst", "node1"])

    Returns:
        Line number (1-indexed) or None if not found
    """
    try:
        # Serialize with standard formatting (2-space indent)
        json_str = json.dumps(json_data, indent=4, sort_keys=True)
        lines = json_str.split("\n")

        # Build regex pattern to find the key at the end of the path
        # We look for the last key in the path, properly quoted
        if not path:
            return None

        target_key = path[-1]
        # Pattern matches: "key": (with optional whitespace)
        pattern = rf'^\s*"{re.escape(target_key)}":\s*'

        # Track which parent keys we've seen to ensure we're in the right context
        parents_to_find = path[:-1]  # All keys except the last one
        parents_found_count = 0

        for i, line in enumerate(lines, start=1):  # 1-indexed line numbers
            # Check if this line contains the next parent key we're looking for
            if parents_found_count < len(parents_to_find):
                parent_pattern = rf'^\s*"{re.escape(parents_to_find[parents_found_count])}":\s*'
                if re.search(parent_pattern, line):
                    parents_found_count += 1
                    # Don't continue - check if target is also on same line (shouldn't happen but be safe)

            # Once we've found all parents, look for the target key
            if parents_found_count == len(parents_to_find):
                if re.search(pattern, line):
                    return i

        # Debug: If we didn't find it, log some info
        LOGGER.debug(
            f"Could not find path {path} in JSON. Found {parents_found_count}/{len(parents_to_find)} parents."
        )
        return None
    except Exception as e:
        LOGGER.debug(f"Error finding JSON path line: {e}")
        return None
