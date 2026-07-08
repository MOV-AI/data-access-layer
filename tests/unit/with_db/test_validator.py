from dal.validation.project_validator import ProjectValidationResult, ProjectValidator
from dal.validation.issues import ProjIssue
import pytest

from typing import Dict, List


class TestProjectValidator:
    def execute_and_assert_same_type_issues(
        self, validator_output: Dict, expected_issues: List[ProjIssue]
    ):
        print(f"Validator output: {validator_output}")

        issue_count = validator_output.summary.total_issues
        assert issue_count == len(
            expected_issues
        ), f"Expected {len(expected_issues)} issues, but got {issue_count}"

        for i in range(issue_count):
            actual_issue = validator_output.issues[i]
            expected_issue = expected_issues[i]

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

    def test_valid_project(self, setup_test_data, setup_test_data_from_path):
        """Tests that a valid project has no issues."""

        validator_output: ProjectValidationResult = ProjectValidator().validate()
        print(f"Validator output: {validator_output}")
        for issue in validator_output.issues:
            print(f"Issue: {issue}")
        assert validator_output.summary.total_issues == 0
        assert len(validator_output.issues) == 0

    def test_duplicated_metadata(self, folder_invalid_data, setup_test_data_from_path):
        """Tests that duplicated metadata is found."""

        from dal.validation.issues import DuplicatedMob

        with setup_test_data_from_path(folder_invalid_data / "proj-duplicated-metadata"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            self.execute_and_assert_same_type_issues(
                validator_output,
                [
                    DuplicatedMob(
                        json_path="check_bool.json",
                        msg="Duplicate MOB name 'check_bool' found in packages: pkg_a, pkg_b installed in workspace 'ros1-workspace'",
                    ),
                ],
            )

    def test_non_matching_ports(self, folder_invalid_data, setup_test_data_from_path):
        """Tests that non matching ports are found."""

        from dal.validation.issues import NonMatchingLinkPorts

        with setup_test_data_from_path(folder_invalid_data / "proj-non-matching-ports"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()

            issue_order = {
                issue.json_path: index for index, issue in enumerate(validator_output.issues)
            }

            self.execute_and_assert_same_type_issues(
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
    def test_missing_node(self, folder_invalid_data, setup_test_data_from_path, path):
        """Tests that missing node issue is found."""
        from dal.validation.issues import MissingMob

        with setup_test_data_from_path(folder_invalid_data / path):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            self.execute_and_assert_same_type_issues(
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

    def test_missing_flow(self, folder_invalid_data, setup_test_data_from_path):
        """Tests that missing flow issue is found."""

        from dal.validation.issues import MissingMob

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-flow"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            self.execute_and_assert_same_type_issues(
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

    def test_missing_flow_instance(self, folder_invalid_data, setup_test_data_from_path):
        """Tests that missing flow instance mentioned in flow is found."""

        from dal.validation.issues import MissingFlowInstance

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-flow-instance"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            self.execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingFlowInstance(
                        json_path="test_missing_flow_instance.json",
                        msg="Link c4087d62-e7f1-4d45-b1a8-caeb5d78137c path references missing flow instance 'non_existing_instance' in Flow 'test_missing_flow_instance'",
                        line_start=18,
                    ),
                ],
            )

    def test_missing_node_instance(self, folder_invalid_data, setup_test_data_from_path):
        """Tests that missing node instance mentioned in flow is found."""

        from dal.validation.issues import MissingNodeInstance

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-node-instance"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            self.execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingNodeInstance(
                        json_path="test_missing_node_instance.json",
                        msg="Link c4087d62-e7f1-4d45-b1a8-caeb5d78137c path references missing node instance 'non_existing_instance' in Flow 'test_missing_node_instance'",
                        line_start=18,
                    ),
                ],
            )

    def test_missing_port(self, folder_invalid_data, setup_test_data_from_path):
        """Tests that missing node port issue is found."""

        from dal.validation.issues import MissingMob

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-port"):
            validator_output: ProjectValidationResult = ProjectValidator().validate()
            self.execute_and_assert_same_type_issues(
                validator_output,
                [
                    MissingMob(
                        json_path="test_missing_port.json",
                        msg="Node 'dependency' missing, required by Flow 'test_missing_port' (instance 'dependency')",
                        line_start=24,
                    ),
                ],
            )
