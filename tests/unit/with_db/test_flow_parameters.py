import pytest

TEST_NODE = "FlowParamTestNode"
FLOW_WITH_PARAM = "test_flow_parameter_with_param"
FLOW_MISSING_PARAM = "test_flow_parameter_missing_param"
PARENT_FLOW = "test_flow_parameter_parent"
CHILD_FLOW = "test_flow_parameter_child"
NODE_INST = "test_node"
CONTAINER = "child"
FLOW_PARAMETER_FLOWS = [
    FLOW_WITH_PARAM,
    FLOW_MISSING_PARAM,
    CHILD_FLOW,
    PARENT_FLOW,
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

    def test_missing_flow_parameter_does_not_fallback_to_parent_flow(
        self, flow_parameter_test_data
    ):
        """
        Test that a subflow does not resolve a missing parameter from its parent flow.
        """
        from dal.exceptions import UndefinedFlowParameterError
        from dal.models.flow import Flow

        with pytest.raises(
            UndefinedFlowParameterError,
            match=f'Flow parameter "param" is not defined in flow "{CHILD_FLOW}"',
        ):
            Flow(PARENT_FLOW).get_node_params(f"{CONTAINER}__{NODE_INST}")
