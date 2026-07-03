from dal.scopes.node import Node
from dal.validation.project_validator import ProjectValidator
from dal.validation.issues import (
    MissingFlowInstance,
    MissingNodeInstance,
    MissingNodePort,
    NonMatchingLinkPorts,
)


class LinkValidator:
    """Link validator class."""

    def __init__(self, project_validator: ProjectValidator, logger):
        self.project_validator = project_validator
        self.logger = logger

    def validate_link(
        self,
        flow_ref: str,
        flow_data: dict,
        flow_content: dict,
        link_id: str,
        from_path: str,
        to_path: str,
    ):
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

        # Parse link paths
        from_info = self._parse_link_path(
            flow_ref, flow_data, flow_content, from_path, "from", link_id
        )
        to_info = self._parse_link_path(flow_ref, flow_data, flow_content, to_path, "to", link_id)

        # Check if parsing succeeded
        if from_info.get("error"):
            self.project_validator.issues.append(from_info["error"])
        if to_info.get("error"):
            self.project_validator.issues.append(to_info["error"])

        # Check if ports exist on the node templates
        src_port_type = from_info.get("port_type")
        dst_port_type = to_info.get("port_type")

        # Check source port existence
        if not src_port_type:
            issue = MissingNodePort(
                json_path=f"{flow_ref}.json",
                msg=f"Source port of link {link_id} does not exist | From: {from_path} | To: {to_path}",
            )
            line_num = self.project_validator._find_json_path_line(
                flow_data, ["Flow", flow_ref, "Links", link_id, "From"]
            )
            if line_num:
                issue.line_start = line_num
            self.project_validator.issues.append(issue)

        # Check destination port existence
        if not dst_port_type:
            issue = MissingNodePort(
                json_path=f"{flow_ref}.json",
                msg=f"Destination port of link {link_id} does not exist | From: {from_path} | To: {to_path}",
            )
            line_num = self.project_validator._find_json_path_line(
                flow_data, ["Flow", flow_ref, "Links", link_id, "To"]
            )
            if line_num:
                issue.line_start = line_num
            self.project_validator.issues.append(issue)

        # Check port compatibility
        if not self._ports_match(src_port_type, dst_port_type):
            issue = NonMatchingLinkPorts(
                json_path=f"{flow_ref}.json",
                msg=f"The ports of link {link_id} in Flow {flow_ref} do not match | From: {from_path} | To: {to_path}",
            )
            line_num = self.project_validator._find_json_path_line(
                flow_data, ["Flow", flow_ref, "Links", link_id]
            )
            if line_num:
                issue.line_start = line_num
            self.project_validator.issues.append(issue)

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
                    issue = MissingFlowInstance(
                        json_path=f"{flow_ref}.json",
                        msg=f"Link {direction} path references missing flow instance "
                        f"'{instance}' in Flow '{flow_ref}'",
                    )

                    if link_id:
                        # Find line number for the link
                        line_num = self.project_validator._find_json_path_line(
                            flow_data, ["Flow", flow_ref, "Links", link_id, direction.capitalize()]
                        )
                        if line_num:
                            issue.line_start = line_num
                    return {"valid": False, "error": issue}

                if instance not in current_flow_data["Container"]:
                    issue = MissingFlowInstance(
                        json_path=f"{flow_ref}.json",
                        msg=f"Flow instance '{instance}' not found in Flow '{flow_ref}' "
                        f"(referenced in link {direction} path)",
                    )

                    if link_id:
                        line_num = self.project_validator._find_json_path_line(
                            flow_data, ["Flow", flow_ref, "Links", link_id, direction.capitalize()]
                        )
                        if line_num:
                            issue.line_start = line_num
                    return {"valid": False, "error": issue}

                # Would need to load the subflow to continue navigation
                # For now, we just verify the instance exists

            # Last instance should be a NodeInst
            final_instance = instances[-1]
            if "NodeInst" not in current_flow_data:
                issue = MissingNodeInstance(
                    json_path=f"{flow_ref}.json",
                    msg=f"Link {direction} path references missing node instance "
                    f"'{final_instance}' in Flow '{flow_ref}'",
                )
                if link_id:
                    line_num = self.project_validator._find_json_path_line(
                        flow_data, ["Flow", flow_ref, "Links", link_id, direction.capitalize()]
                    )
                    if line_num:
                        issue.line_start = line_num
                return {"valid": False, "error": issue}

            if final_instance not in current_flow_data["NodeInst"]:
                issue = MissingNodeInstance(
                    json_path=f"{flow_ref}.json",
                    msg=f"Node instance '{final_instance}' not found in Flow '{flow_ref}' "
                    f"(referenced in link {direction} path)",
                )
                if link_id:
                    line_num = self.project_validator._find_json_path_line(
                        flow_data, ["Flow", flow_ref, "Links", link_id, direction.capitalize()]
                    )
                    if line_num:
                        issue.line_start = line_num
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

        except Exception as e:
            self.logger.warning(f"Error parsing link path {path}: {e}")
            return {"valid": False}

    def _get_port_type(self, node_template: str, port_name: str) -> dict:
        """
        Get port type information from a Node template.

        Args:
            node_template: Name of the Node template
            port_name: Name of the port

        Returns:
            Port type dictionary or empty dict if port not found
        """
        try:
            if not self.project_validator._object_exists("Node", node_template):
                return {}

            node = Node(node_template)
            node_data = node.serialize()

            if "Node" not in node_data or node_template not in node_data["Node"]:
                return {}

            node_content = node_data["Node"][node_template]

            # Check if port exists in PortsInst
            if "PortsInst" in node_content and port_name in node_content["PortsInst"]:
                return node_content["PortsInst"][port_name]

            return {}

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
