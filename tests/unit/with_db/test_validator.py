from dal.validation.project_validator import ProjectValidationResult, ProjectValidator
from dal.validation.issues import ProjIssue
import pytest
from pathlib import Path
from contextlib import contextmanager

from typing import Dict, List


@pytest.fixture(autouse=True)
def isolated_database(global_db):
    """Ensure each test runs in an isolated database environment."""

    from dal.movaidb.database import MovaiDB
    from dal.scopes.package import Package
    from dal.validation.project_validator import VALIDATED_SCOPES

    isolated_db = MovaiDB()

    def clear():
        Package.clear_packagedata()
        for scope in VALIDATED_SCOPES:
            try:
                isolated_db.delete_by_args(scope, Name="*")
            except Exception as e:
                print(f"Failed to remove scope data for {scope}: {e}")

    clear()
    yield
    clear()


@contextmanager
def setup_test_data_from_path(path: Path):
    """Import test metadata from a given path before each test."""

    from dal.tools.backup import Importer
    from dal.scopes.node import Node
    from dal.scopes.flow import Flow
    from dal.scopes.package import Package

    # Ensure package tracking does not leak between tests.
    Package.clear_packagedata()

    # Find all packages in the path (each subdirectory with metadata/ folder)
    packages = [p for p in path.iterdir() if p.is_dir() and (p / "metadata").exists()]

    all_nodes = []
    all_flows = []

    # Import from each package
    for package in packages:
        metadata_path = package / "metadata"
        nodes = []
        flows = []

        # Scan for Flows and Nodes
        flow_dir = metadata_path / "Flow"
        node_dir = metadata_path / "Node"

        if flow_dir.exists():
            flows = [f.stem for f in flow_dir.glob("*.json")]
            all_flows.extend(flows)

        if node_dir.exists():
            nodes = [n.stem for n in node_dir.glob("*.json")]
            all_nodes.extend(nodes)

        # Import metadata using Importer
        importer = Importer(
            metadata_path,
            force=True,
            dry=False,
            debug=False,
            recursive=True,
            clean_old_data=False,  # Don't clean between packages
        )

        # Import nodes first (flows may depend on them)
        if nodes:
            importer.run({"Node": nodes})

        # Then import flows
        if flows:
            importer.run({"Flow": flows})

    try:
        yield
    finally:
        # Cleanup after test
        for node_name in all_nodes:
            try:
                node = Node(node_name)
                node.remove(force=True)
            except Exception as e:
                print(f"Failed to remove node {node_name} during cleanup: {e}")

        for flow_name in all_flows:
            try:
                flow = Flow(flow_name)
                flow.remove(force=True)
            except Exception as e:
                print(f"Failed to remove flow {flow_name} during cleanup: {e}")

        Package.clear_packagedata()


def execute_and_assert_same_type_issues(validator_output: Dict, expected_issues: List[ProjIssue]):
    print(f"Validator output: {validator_output}")

    issue_count = validator_output.summary.total_issues
    assert issue_count == len(
        expected_issues
    ), f"Expected {len(expected_issues)} issues, but got {issue_count}: {validator_output.issues}"

    for i in range(issue_count):
        actual_issue = validator_output.issues[i]
        expected_issue = expected_issues[i]

        expected_document_name = Path(expected_issue.json_path).stem
        expected_document_type = (
            None if expected_issue.iss_type == "Duplicated metadata" else "Flow"
        )

        print(actual_issue.json_path)
        print(f"Actual issue: {actual_issue}")
        print(f"Expected issue: {expected_issue}")

        assert (
            expected_issue.msg in actual_issue.msg
        ), f"Expected message '{expected_issue.msg}', but got '{actual_issue.msg}'"
        assert (
            actual_issue.severity == expected_issue.severity
        ), f"Expected severity '{expected_issue.severity}', but got '{actual_issue.severity}'"
        assert (
            actual_issue.json_path == expected_issue.json_path
        ), f"Expected json_path '{expected_issue.json_path}', but got '{actual_issue.json_path}'"
        assert (
            actual_issue.category == expected_issue.category
        ), f"Expected category '{expected_issue.category}', but got '{actual_issue.category}'"
        assert (
            actual_issue.iss_type == expected_issue.iss_type
        ), f"Expected iss_type '{expected_issue.iss_type}', but got '{actual_issue.iss_type}'"
        assert (
            actual_issue.line_start == expected_issue.line_start
        ), f"Expected line_start '{expected_issue.line_start}', but got '{actual_issue.line_start}'"
        assert (
            actual_issue.document_name == expected_document_name
        ), f"Expected document_name '{expected_document_name}', but got '{actual_issue.document_name}'"
        if expected_document_type is not None:
            assert (
                actual_issue.document_type == expected_document_type
            ), f"Expected document_type '{expected_document_type}', but got '{actual_issue.document_type}'"
        else:
            assert actual_issue.document_type not in {
                "",
                "Unknown",
                None,
            }, "Expected duplicate issue to have a concrete document_type"


class TestProjectValidator:
    def test_valid_project(self, setup_test_data):
        """Tests that a valid project has no issues."""

        validator_output: ProjectValidationResult = ProjectValidator().validate()
        print(f"Validator output: {validator_output}")
        for issue in validator_output.issues:
            print(f"Issue: {issue}")
        assert (
            validator_output.summary.total_issues == 0
        ), f"Expected 0 issues, but got {validator_output.summary.total_issues}: {validator_output.issues}"
        assert len(validator_output.issues) == 0

    def test_duplicated_metadata(self, isolated_database, folder_invalid_data):
        """Tests that duplicated metadata is found."""

        from dal.validation.issues import DuplicatedMob

        with setup_test_data_from_path(folder_invalid_data / "proj-duplicated-metadata"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            execute_and_assert_same_type_issues(
                validator_output,
                [
                    DuplicatedMob(
                        json_path="check_bool.json",
                        msg="Duplicate MOB name 'check_bool' found in packages: pkg_a, pkg_b installed in workspace 'unknown'",
                    ),
                ],
            )

    def test_non_matching_ports(self, isolated_database, folder_invalid_data):
        """Tests that non matching ports are found."""

        from dal.validation.issues import NonMatchingLinkPorts

        with setup_test_data_from_path(folder_invalid_data / "proj-non-matching-ports"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()

            issue_order = {
                issue.json_path: index for index, issue in enumerate(validator_output.issues)
            }

            execute_and_assert_same_type_issues(
                validator_output,
                sorted(
                    [
                        NonMatchingLinkPorts(
                            json_path="test_transition_to_ros.json",
                            msg="The ports of link 20893b58-911b-470d-9306-1e4ac32b76d1 in Flow test_transition_to_ros do not match | From: start/start/start | To: ros/sub/in",
                            line_start=15,
                        ),
                        NonMatchingLinkPorts(
                            json_path="test_transition_to_any.json",
                            msg="The ports of link 8395d1a2-af21-4b12-a1a3-e2dfbf7c198f in Flow test_transition_to_any do not match | From: start/start/start | To: test_any/sub/in",
                            line_start=15,
                        ),
                        NonMatchingLinkPorts(
                            json_path="test_pub_ros_to_sub_ros.json",
                            msg="The ports of link ca35667e-8e58-4c71-8973-245da65dbe0b in Flow test_pub_ros_to_sub_ros do not match | From: ros/pub_empty/out | To: ros/sub/in",
                            line_start=15,
                        ),
                        NonMatchingLinkPorts(
                            json_path="test_transition_to_dependency.json",
                            msg="The ports of link 20893b58-911b-470d-9306-1e4ac32b76d1 in Flow test_transition_to_dependency do not match | From: start/start/start | To: dep/dependency/in",
                            line_start=15,
                        ),
                    ],
                    key=lambda issue: issue_order[issue.json_path],
                ),
            )

    @pytest.mark.parametrize("path", ["proj-missing-node"])
    def test_missing_node(self, isolated_database, folder_invalid_data, path):
        """Tests that missing node issue is found."""
        from dal.validation.issues import MissingMob

        with setup_test_data_from_path(folder_invalid_data / path):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingMob(
                        json_path="test_missing_node.json",
                        msg="Node 'test_any' missing, required by Flow 'test_missing_node' (instance 'test_any')",
                        line_start=27,
                    ),
                    MissingMob(
                        json_path="test_missing_node.json",
                        msg="Node 'test_any' missing, required by Flow 'test_missing_node' (instance 'test_something')",
                        line_start=39,
                    ),
                ],
            )

    def test_missing_flow(self, isolated_database, folder_invalid_data):
        """Tests that missing flow issue is found."""

        from dal.validation.issues import MissingMob

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-flow"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingMob(
                        json_path="test_missing_flow.json",
                        msg="Flow 'device_api' missing, required by Flow 'test_missing_flow' (instance 'device_api')",
                        line_start=6,
                    ),
                    MissingMob(
                        json_path="test_missing_flow.json",
                        msg="Flow 'tugbot' missing, required by Flow 'test_missing_flow' (instance 'tugbot')",
                        line_start=18,
                    ),
                ],
            )

    def test_missing_flow_instance(self, isolated_database, folder_invalid_data):
        """Tests that missing flow instance mentioned in flow is found."""

        from dal.validation.issues import MissingFlowInstance

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-flow-instance"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingFlowInstance(
                        json_path="test_missing_flow_instance.json",
                        msg="Link c4087d62-e7f1-4d45-b1a8-caeb5d78137c path references missing flow instance 'non_existing_instance' in Flow 'test_missing_flow_instance'",
                        line_start=18,
                    ),
                ],
            )

    def test_missing_node_instance(self, isolated_database, folder_invalid_data):
        """Tests that missing node instance mentioned in flow is found."""

        from dal.validation.issues import MissingNodeInstance

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-node-instance"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingNodeInstance(
                        json_path="test_missing_node_instance.json",
                        msg="Link c4087d62-e7f1-4d45-b1a8-caeb5d78137c path references missing node instance 'non_existing_instance' in Flow 'test_missing_node_instance'",
                        line_start=18,
                    ),
                ],
            )

    def test_missing_port(self, isolated_database, folder_invalid_data):
        """Tests that missing node port issue is found."""

        from dal.validation.issues import MissingMob

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-port"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingMob(
                        json_path="test_missing_port.json",
                        msg="Node 'dependency' missing, required by Flow 'test_missing_port' (instance 'dependency')",
                        line_start=24,
                    ),
                ],
            )

    def test_missing_referenced_parameters(self, isolated_database, folder_invalid_data):
        """Tests that missing flow parameters are found."""

        from dal.validation.issues import MissingReferencedParameter

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-referenced-params"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            validator_output.issues.sort(key=lambda issue: issue.line_start)
            print(f"Validator output: {validator_output}")

            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingReferencedParameter(
                        json_path="test_missing_referenced_parameters.json",
                        msg="Node instance 'dependency' parameter 'missing_compound_param' has an undefined param reference in Flow 'test_missing_referenced_parameters'",
                        line_start=27,
                    ),
                    MissingReferencedParameter(
                        json_path="test_missing_referenced_parameters.json",
                        msg="Node instance 'dependency' parameter 'missing_flow_parameter' has an undefined flow reference in Flow 'test_missing_referenced_parameters'",
                        line_start=31,
                    ),
                    MissingReferencedParameter(
                        json_path="test_missing_referenced_parameters.json",
                        msg="Node instance 'dependency' parameter 'missing_var_parameter' has an undefined var reference in Flow 'test_missing_referenced_parameters'",
                        line_start=35,
                    ),
                    MissingReferencedParameter(
                        json_path="test_missing_referenced_parameters.json",
                        msg="Flow 'test_missing_referenced_parameters' parameter 'missing_config_parameter' has an undefined config reference in Flow 'test_missing_referenced_parameters'",
                        line_start=52,
                    ),
                ],
            )


class TestFlowValidator:
    def test_validate_non_existing_flow(self, global_db, setup_test_data):
        """Tests that validating a non-existing flow raises an exception."""

        from dal.validation.flow_validator import FlowValidator

        with pytest.raises(Exception) as exc_info:
            FlowValidator("non_existing_flow").validate_flow()

        assert "non_existing_flow does not exist" in str(
            exc_info.value
        ), f"Expected error message to contain 'non_existing_flow does not exist', but got: {exc_info.value}"

    def test_flow_with_valid_links(self, global_db, setup_test_data):
        """Tests that a flow with valid links has no issues."""

        from dal.validation.flow_validator import FlowValidator

        validator_output: ProjectValidationResult = FlowValidator(
            "flow_with_nodes_and_subflow"
        ).validate_flow()
        print(f"Validator output: {validator_output}")
        for issue in validator_output.issues:
            print(f"Issue: {issue}")
        assert (
            validator_output.summary.total_issues == 0
        ), f"Expected 0 issues, but got {validator_output.summary.total_issues}: {validator_output.issues}"
        assert len(validator_output.issues) == 0

    def test_flow_with_invalid_links(self, global_db, folder_invalid_data):
        """Tests that a flow with invalid links has issues."""

        from dal.validation.issues import NonMatchingLinkPorts
        from dal.validation.flow_validator import FlowValidator

        with setup_test_data_from_path(folder_invalid_data / "proj-non-matching-ports"):
            validator_output: ProjectValidationResult = FlowValidator(
                "test_transition_to_ros"
            ).validate_flow()
            execute_and_assert_same_type_issues(
                validator_output,
                [
                    NonMatchingLinkPorts(
                        json_path="test_transition_to_ros.json",
                        msg="The ports of link 20893b58-911b-470d-9306-1e4ac32b76d1 in Flow test_transition_to_ros do not match | From: start/start/start | To: ros/sub/in",
                        line_start=15,
                    ),
                ],
            )

    def test_flow_with_missing_node(self, global_db, folder_invalid_data):
        """Tests that a flow with invalid links has issues."""

        from dal.validation.issues import MissingMob
        from dal.validation.flow_validator import FlowValidator

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-node"):
            validator_output: ProjectValidationResult = FlowValidator(
                "test_missing_node"
            ).validate_flow()
            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingMob(
                        json_path="test_missing_node.json",
                        msg="Node 'test_any' missing, required by Flow 'test_missing_node' (instance 'test_any')",
                        line_start=27,
                    ),
                    MissingMob(
                        json_path="test_missing_node.json",
                        msg="Node 'test_any' missing, required by Flow 'test_missing_node' (instance 'test_something')",
                        line_start=39,
                    ),
                ],
            )

    def test_flow_with_missing_port(self, global_db, folder_invalid_data):
        """Tests that a flow with invalid links has issues."""

        from dal.validation.issues import MissingMob
        from dal.validation.flow_validator import FlowValidator

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-port"):
            validator_output: ProjectValidationResult = FlowValidator(
                "test_missing_port"
            ).validate_flow()
            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingMob(
                        json_path="test_missing_port.json",
                        msg="Node 'dependency' missing, required by Flow 'test_missing_port' (instance 'dependency')",
                        line_start=24,
                    ),
                ],
            )

    def test_flow_with_missing_flow_instance(self, global_db, folder_invalid_data):
        """Tests that a flow with invalid links has issues."""

        from dal.validation.issues import MissingFlowInstance
        from dal.validation.flow_validator import FlowValidator

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-flow-instance"):
            validator_output: ProjectValidationResult = FlowValidator(
                "test_missing_flow_instance"
            ).validate_flow()
            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingFlowInstance(
                        json_path="test_missing_flow_instance.json",
                        msg="Link c4087d62-e7f1-4d45-b1a8-caeb5d78137c path references missing flow instance 'non_existing_instance' in Flow 'test_missing_flow_instance'",
                        line_start=18,
                    ),
                ],
            )

    def test_flow_with_missing_node_instance(self, global_db, folder_invalid_data):
        """Tests that a flow with invalid links has issues."""

        from dal.validation.issues import MissingNodeInstance
        from dal.validation.flow_validator import FlowValidator

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-node-instance"):
            validator_output: ProjectValidationResult = FlowValidator(
                "test_missing_node_instance"
            ).validate_flow()
            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingNodeInstance(
                        json_path="test_missing_node_instance.json",
                        msg="Link c4087d62-e7f1-4d45-b1a8-caeb5d78137c path references missing node instance 'non_existing_instance' in Flow 'test_missing_node_instance'",
                        line_start=18,
                    ),
                ],
            )

    def test_flow_with_missing_flow(self, global_db, folder_invalid_data):
        """Tests that a flow with invalid links has issues."""

        from dal.validation.issues import MissingMob
        from dal.validation.flow_validator import FlowValidator

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-flow"):
            validator_output: ProjectValidationResult = FlowValidator(
                "test_missing_flow"
            ).validate_flow()
            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingMob(
                        json_path="test_missing_flow.json",
                        msg="Flow 'device_api' missing, required by Flow 'test_missing_flow' (instance 'device_api')",
                        line_start=6,
                    ),
                    MissingMob(
                        json_path="test_missing_flow.json",
                        msg="Flow 'tugbot' missing, required by Flow 'test_missing_flow' (instance 'tugbot')",
                        line_start=18,
                    ),
                ],
            )

    def test_flow_with_missing_referenced_parameters(self, global_db, folder_invalid_data):
        """Tests that a flow with missing referenced parameters has issues."""

        from dal.validation.issues import MissingReferencedParameter
        from dal.validation.flow_validator import FlowValidator

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-referenced-params"):
            validator_output: ProjectValidationResult = FlowValidator(
                "test_missing_referenced_parameters"
            ).validate_flow()
            validator_output.issues.sort(key=lambda issue: issue.line_start)
            print(f"Validator output: {validator_output}")

            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingReferencedParameter(
                        json_path="test_missing_referenced_parameters.json",
                        msg="Node instance 'dependency' parameter 'missing_compound_param' has an undefined param reference in Flow 'test_missing_referenced_parameters'",
                        line_start=27,
                    ),
                    MissingReferencedParameter(
                        json_path="test_missing_referenced_parameters.json",
                        msg="Node instance 'dependency' parameter 'missing_flow_parameter' has an undefined flow reference in Flow 'test_missing_referenced_parameters'",
                        line_start=31,
                    ),
                    MissingReferencedParameter(
                        json_path="test_missing_referenced_parameters.json",
                        msg="Node instance 'dependency' parameter 'missing_var_parameter' has an undefined var reference in Flow 'test_missing_referenced_parameters'",
                        line_start=35,
                    ),
                    MissingReferencedParameter(
                        json_path="test_missing_referenced_parameters.json",
                        msg="Flow 'test_missing_referenced_parameters' parameter 'missing_config_parameter' has an undefined config reference in Flow 'test_missing_referenced_parameters'",
                        line_start=52,
                    ),
                ],
            )

    def test_flow_with_missing_referenced_parameters_in_subflow(
        self, global_db, folder_invalid_data
    ):
        """Tests that validating a flow also validates nested subflows."""

        from dal.validation.issues import MissingReferencedParameter
        from dal.validation.flow_validator import FlowValidator

        with setup_test_data_from_path(
            folder_invalid_data / "proj-subflow-missing-referenced-params"
        ):
            validator_output: ProjectValidationResult = FlowValidator(
                "test_parent_with_invalid_subflow"
            ).validate_flow()

            execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingReferencedParameter(
                        json_path="test_invalid_parameter_subflow.json",
                        msg="Flow 'test_invalid_parameter_subflow' parameter 'missing_config_parameter' has an undefined config reference in Flow 'test_invalid_parameter_subflow'",
                        line_start=19,
                    ),
                ],
            )
