from dal.validation.project_validator import ProjectValidator
import pytest
from pathlib import Path

from typing import Dict


class TestProjectValidator:
    def execute_and_assert_same_type_issues(
        self, validator_output: Dict, expected_issues_count, expected_severity, expected_issue_type
    ):
        print(f"Validator output: {validator_output}")

        issue_count = validator_output["summary"]["total_issues"]
        assert (
            issue_count == expected_issues_count
        ), f"Expected {expected_issues_count} issues, but got {issue_count}"

        for issue in validator_output["issues"]:
            print(f"Checking issue: {issue}")  # Debugging line to print each issue
            assert (
                issue.severity == expected_severity
            ), f"Expected severity {expected_severity}, but got {issue.severity}"
            assert isinstance(
                issue, expected_issue_type
            ), f"Expected issue type {expected_issue_type.__name__}, but got {type(issue).__name__}"

        return validator_output

    def test_non_matching_ports(self, folder_invalid_data, setup_test_data_from_path):
        """Tests that non matching ports are found."""

        from dal.validation.issues import NonMatchingLinkPorts, Severity

        with setup_test_data_from_path(folder_invalid_data / "proj-non-matching-ports"):
            validator_output = ProjectValidator().validate()
            test_exec = self.execute_and_assert_same_type_issues(
                validator_output, 4, Severity.ERROR, NonMatchingLinkPorts
            )

            # assert of issue per file
            iss_str_paths = [Path(str(iss.json_path)).name for iss in test_exec["issues"]]
            assert "test_pub_ros_to_sub_ros.json" in iss_str_paths
            assert "test_transition_to_ros.json" in iss_str_paths
            assert "test_transition_to_dependency.json" in iss_str_paths
            assert "test_transition_to_any.json" in iss_str_paths

    @pytest.mark.parametrize("path", ["proj-missing-node"])
    def test_missing_node(self, folder_invalid_data, setup_test_data_from_path, path):
        """Tests that missing node issue is found."""
        from dal.validation.issues import MissingMob, Severity

        with setup_test_data_from_path(folder_invalid_data / path):
            validator_output = ProjectValidator().validate()
            self.execute_and_assert_same_type_issues(
                validator_output, 2, Severity.ERROR, MissingMob
            )

    def test_missing_flow(self, folder_invalid_data, setup_test_data_from_path):
        """Tests that missing flow issue is found."""

        from dal.validation.issues import MissingMob, Severity

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-flow"):
            validator_output = ProjectValidator().validate()
            self.execute_and_assert_same_type_issues(
                validator_output, 2, Severity.ERROR, MissingMob
            )

    def test_missing_flow_instance(self, folder_invalid_data, setup_test_data_from_path):
        """Tests that missing flow instance mentioned in flow is found."""

        from dal.validation.issues import MissingFlowInstance, Severity

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-flow-instance"):
            validator_output = ProjectValidator().validate()
            self.execute_and_assert_same_type_issues(
                validator_output, 1, Severity.ERROR, MissingFlowInstance
            )

    def test_missing_node_instance(self, folder_invalid_data, setup_test_data_from_path):
        """Tests that missing node instance mentioned in flow is found."""

        from dal.validation.issues import MissingNodeInstance, Severity

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-node-instance"):
            validator_output = ProjectValidator().validate()
            self.execute_and_assert_same_type_issues(
                validator_output, 1, Severity.ERROR, MissingNodeInstance
            )

    def test_missing_port(self, folder_invalid_data, setup_test_data_from_path):
        """Tests that missing node port issue is found."""

        from dal.validation.issues import MissingMob, Severity

        with setup_test_data_from_path(folder_invalid_data / "proj-missing-port"):
            validator_output = ProjectValidator().validate()
            self.execute_and_assert_same_type_issues(
                validator_output, 1, Severity.ERROR, MissingMob
            )
