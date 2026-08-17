import pytest

TEST_NODE = "FlowParamTestNode"
FLOW_WITH_PARAM = "test_flow_parameter_with_param"
FLOW_MISSING_PARAM = "test_flow_parameter_missing_param"
PARENT_FLOW = "test_flow_parameter_parent"
PARENT_FLOW_WITH_CONTAINER_PARAM = "test_flow_parameter_parent_with_container_param"
NESTED_PARENT_FLOW = "test_flow_parameter_nested_parent"
NESTED_MISSING_PARENT_FLOW = "test_flow_parameter_nested_missing_parent"
NESTED_MISSING_CHILD_FLOW = "test_flow_parameter_nested_missing_child"
NESTED_PARENT_FLOW_WITH_ANCESTOR_CONTAINER_PARAM = (
    "test_flow_parameter_nested_parent_with_ancestor_container_param"
)
NESTED_CHILD_FLOW = "test_flow_parameter_nested_child"
NESTED_GRANDCHILD_FLOW = "test_flow_parameter_nested_grandchild"
CHILD_FLOW = "test_flow_parameter_child"
NODE_INST = "test_node"
CONTAINER = "child"
FLOW_PARAMETER_FLOWS = [
    FLOW_WITH_PARAM,
    FLOW_MISSING_PARAM,
    CHILD_FLOW,
    PARENT_FLOW,
    PARENT_FLOW_WITH_CONTAINER_PARAM,
    NESTED_PARENT_FLOW,
    NESTED_MISSING_PARENT_FLOW,
    NESTED_MISSING_CHILD_FLOW,
    NESTED_PARENT_FLOW_WITH_ANCESTOR_CONTAINER_PARAM,
    NESTED_CHILD_FLOW,
    NESTED_GRANDCHILD_FLOW,
]
FLOW_PARAMETER_NODES = [TEST_NODE]


@pytest.fixture()
def flow_parameter_test_data(global_db, metadata_folder_flow_parameters):
    """Import the minimal node/flow graph needed by the flow parameter tests."""

    from dal.scopes.flow import Flow
    from dal.scopes.node import Node
    from dal.scopes.package import Package
    from dal.tools.backup import Importer

    Package.clear_packagedata()

    importer = Importer(
        metadata_folder_flow_parameters,
        force=True,
        dry=False,
        debug=False,
        recursive=True,
        clean_old_data=True,
    )
    importer.run({"Node": FLOW_PARAMETER_NODES})
    importer.run({"Flow": FLOW_PARAMETER_FLOWS})

    yield

    for flow_name in FLOW_PARAMETER_FLOWS:
        try:
            Flow(flow_name).remove(force=True)
        except Exception:
            print(f"Failed to remove flow {flow_name} during cleanup.")

    for node_name in FLOW_PARAMETER_NODES:
        try:
            Node(node_name).remove(force=True)
        except Exception:
            print(f"Failed to remove node {node_name} during cleanup.")

    Package.clear_packagedata()


class TestFlowParameters:
    def test_flow_parameter_exists(self, flow_parameter_test_data):
        """
        Test that a parameter defined in the flow is parsed correctly.
        """
        from dal.models.flow import Flow

        params = Flow(FLOW_WITH_PARAM).get_node_params(NODE_INST)

        assert params["log_description"] == "Parameter is parsed correctly"

    def test_missing_flow_parameter_raises_error(self, flow_parameter_test_data):
        """
        Test that a missing parameter in the current flow raises an error.
        """
        from dal.exceptions import UndefinedFlowParameterError
        from dal.models.flow import Flow

        with pytest.raises(
            UndefinedFlowParameterError,
            match=f'Flow parameter "param" is not defined in flow "{FLOW_MISSING_PARAM}"',
        ):
            Flow(FLOW_MISSING_PARAM).get_node_params(NODE_INST)

    def test_missing_flow_parameter_returns_unresolved_when_errors_disabled(
        self, flow_parameter_test_data, monkeypatch
    ):
        """
        Test that disabled validation preserves the old unresolved flow parameter value.
        """
        from dal.models.flow import Flow

        monkeypatch.setenv("RAISE_FLOW_VALIDATION_ERRORS", "False")

        params = Flow(FLOW_MISSING_PARAM).get_node_params(NODE_INST)

        assert params["log_description"] == "Parameter is $(flow param)"

    def test_flow_parameter_can_be_resolved_from_direct_parent_flow(self, flow_parameter_test_data):
        """
        Test that a subflow can resolve a missing parameter from its direct parent flow.
        """
        from dal.models.flow import Flow

        params = Flow(PARENT_FLOW).get_node_params(f"{CONTAINER}__{NODE_INST}")

        assert params["log_description"] == "Parameter is parent value"

    def test_flow_parameter_does_not_skip_missing_direct_parent_flow(
        self, flow_parameter_test_data
    ):
        """
        Test that a subflow does not skip a missing parent parameter to use a grandparent value.
        """
        from dal.exceptions import UndefinedFlowParameterError
        from dal.models.flow import Flow

        with pytest.raises(
            UndefinedFlowParameterError,
            match=f'Flow parameter "param" is not defined in flow "{NESTED_MISSING_CHILD_FLOW}"',
        ):
            Flow(NESTED_MISSING_PARENT_FLOW).get_node_params("child__grandchild__test_node")

    def test_missing_direct_parent_flow_uses_old_inheritance_when_errors_disabled(
        self, flow_parameter_test_data, monkeypatch
    ):
        """
        Test that disabled validation preserves the old grandparent fallback behavior.
        """
        from dal.models.flow import Flow

        monkeypatch.setenv("RAISE_FLOW_VALIDATION_ERRORS", "False")

        params = Flow(NESTED_MISSING_PARENT_FLOW).get_node_params("child__grandchild__test_node")

        assert params["log_description"] == "Parameter is grandparent value"

    def test_flow_parameter_can_be_bound_by_parent_container(self, flow_parameter_test_data):
        """
        Test that a subflow parameter can be bound by the parent container.
        """
        from dal.models.flow import Flow

        params = Flow(PARENT_FLOW_WITH_CONTAINER_PARAM).get_node_params(f"{CONTAINER}__{NODE_INST}")

        assert params["log_description"] == "Parameter is parent value"

    def test_flow_parameter_can_be_resolved_through_explicit_pass_through_chain(
        self, flow_parameter_test_data
    ):
        """
        Test that nested subflows can explicitly pass a flow parameter up one level at a time.
        """
        from dal.models.flow import Flow

        params = Flow(NESTED_PARENT_FLOW).get_node_params("child__grandchild__test_node")

        assert params["log_description"] == "Parameter is nested parent value"

    def test_flow_parameter_can_be_bound_by_ancestor_container_through_pass_through_chain(
        self, flow_parameter_test_data
    ):
        """
        Test nested subflows can pass a parameter through to an ancestor container binding.
        """
        from dal.models.flow import Flow

        params = Flow(NESTED_PARENT_FLOW_WITH_ANCESTOR_CONTAINER_PARAM).get_node_params(
            "child__grandchild__test_node"
        )

        assert params["log_description"] == "Parameter is ancestor container value"
