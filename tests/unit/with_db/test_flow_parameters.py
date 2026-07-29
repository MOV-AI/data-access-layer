import pytest


TEST_NODE = "FlowParamTestNode"
FLOW_WITH_PARAM = "test_flow_parameter_with_param"
FLOW_MISSING_PARAM = "test_flow_parameter_missing_param"
PARENT_FLOW = "test_flow_parameter_parent"
CHILD_FLOW = "test_flow_parameter_child"
NODE_INST = "test_node"
CONTAINER = "child"


@pytest.fixture()
def flow_parameter_test_data(global_db):
    """Create the minimal node/flow graph needed by the flow parameter tests."""

    global_db.set(
        {
            "Node": {
                TEST_NODE: {
                    "Label": TEST_NODE,
                    "Type": "MovAI/State",
                    "Parameter": {
                        "log_description": {
                            "Type": "string",
                            "Value": "default",
                        }
                    },
                }
            },
            "Flow": {
                FLOW_WITH_PARAM: {
                    "Label": FLOW_WITH_PARAM,
                    "NodeInst": {
                        NODE_INST: {
                            "NodeLabel": NODE_INST,
                            "Template": TEST_NODE,
                            "Parameter": {
                                "log_description": {
                                    "Type": "string",
                                    "Value": "Parameter is $(flow param)",
                                }
                            },
                        }
                    },
                    "Parameter": {
                        "param": {
                            "Description": "",
                            "Type": "string",
                            "Value": "parsed correctly",
                        }
                    },
                },
                FLOW_MISSING_PARAM: {
                    "Label": FLOW_MISSING_PARAM,
                    "NodeInst": {
                        NODE_INST: {
                            "NodeLabel": NODE_INST,
                            "Template": TEST_NODE,
                            "Parameter": {
                                "log_description": {
                                    "Type": "string",
                                    "Value": "Parameter is $(flow param)",
                                }
                            },
                        }
                    },
                },
                PARENT_FLOW: {
                    "Label": PARENT_FLOW,
                    "Container": {
                        CONTAINER: {
                            "ContainerFlow": CHILD_FLOW,
                            "ContainerLabel": CONTAINER,
                        }
                    },
                    "Parameter": {
                        "param": {
                            "Description": "",
                            "Type": "string",
                            "Value": "parent value",
                        }
                    },
                },
                CHILD_FLOW: {
                    "Label": CHILD_FLOW,
                    "NodeInst": {
                        NODE_INST: {
                            "NodeLabel": NODE_INST,
                            "Template": TEST_NODE,
                            "Parameter": {
                                "log_description": {
                                    "Type": "string",
                                    "Value": "Parameter is $(flow param)",
                                }
                            },
                        }
                    },
                },
            },
        }
    )

    yield

    for flow_name in [FLOW_WITH_PARAM, FLOW_MISSING_PARAM, PARENT_FLOW, CHILD_FLOW]:
        global_db.delete({"Flow": {flow_name: {}}})

    global_db.delete({"Node": {TEST_NODE: {}}})


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
