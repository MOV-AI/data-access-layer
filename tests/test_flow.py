import unittest
from unittest.mock import MagicMock, patch

from dal.helpers.flow.gflow import GFlow
from dal.models.flow import Flow
from dal.models.scopestree import scopes


class FlowTests(unittest.TestCase):
    maxDiff = None

    # @patch("dal.models.nodeinst.NodeInst.node_template")
    def test_no_remap_two_inports(self):  # , mock_node_template: MagicMock):
        # mock_node_template.is_remappable = True
        # mock_node_template.get_params = lambda: Exception("get_params")

        node_pub1 = {
            "Node": {
                "NodePub1": {
                    "Info": "First publisher",
                    "Label": "nodepub1",
                    "LastUpdate": "04/06/2020 at 07:10:28",
                    "PortsInst": {
                        "pubport": {
                            "Message": "Float32",
                            "Out": {"out": {"Message": "std_msgs/Float32"}},
                            "Package": "std_msgs",
                            "Template": "ROS1/Publisher",
                        }
                    },
                    "Type": "ROS1/Node",
                    "Remappable": True,
                }
            }
        }

        node_pub2 = {
            "Node": {
                "NodePub2": {
                    "Info": "Second publisher",
                    "Label": "nodepub2",
                    "LastUpdate": "04/06/2020 at 07:10:28",
                    "PortsInst": {
                        "pubport": {
                            "Message": "Float32",
                            "Out": {"out": {"Message": "std_msgs/Float32"}},
                            "Package": "std_msgs",
                            "Template": "ROS1/Publisher",
                        }
                    },
                    "Type": "ROS1/Node",
                    "Remappable": True,
                }
            }
        }

        node_sub1 = {
            "Node": {
                "NodeSub1": {
                    "Info": "First subscriber",
                    "Label": "nodesub1",
                    "LastUpdate": "04/06/2020 at 07:10:28",
                    "PortsInst": {
                        "subport": {
                            "Message": "Float32",
                            "In": {
                                "in": {"Callback": "place_holder", "Message": "std_msgs/Float32"}
                            },
                            "Package": "std_msgs",
                            "Template": "ROS1/Subscriber",
                        }
                    },
                    "Type": "ROS1/Node",
                    "Remappable": True,
                }
            }
        }

        node_sub2 = {
            "Node": {
                "NodeSub2": {
                    "Info": "Second subscriber",
                    "Label": "nodesub2",
                    "LastUpdate": "04/06/2020 at 07:10:28",
                    "PortsInst": {
                        "subport": {
                            "Message": "Float32",
                            "In": {
                                "in": {"Callback": "place_holder", "Message": "std_msgs/Float32"}
                            },
                            "Package": "std_msgs",
                            "Template": "ROS1/Subscriber",
                        }
                    },
                    "Type": "ROS1/Node",
                    "Remappable": True,
                }
            }
        }

        flow = {
            "Flow": {
                "two_pubs_test": {
                    "Description": "Test two out ports to same in port",
                    "ExposedPorts": {
                        "NodePub1": {"nodepub1": ["pubport/out"]},
                        "NodePub2": {"nodepub2": ["pubport/out"]},
                        "NodeSub1": {"nodesub1": ["subport/in"]},
                        "NodeSub2": {"nodesub2": ["subport/in"]},
                    },
                    "Label": "two_pubs_test",
                    "LastUpdate": "09/10/2020 at 12:24:44",
                    "Links": {
                        "06eed84a-1a7f-4ad1-95e1-e1e8d1c62ea3": {
                            "From": "nodepub1/pubport/out",
                            "To": "nodesub1/subport/in",
                        },
                        "652744ed-63cd-463d-9eba-45b6e7f7ea7d": {
                            "From": "nodepub1/pubport/out",
                            "To": "nodesub2/subport/in",
                        },
                        "070ab147-280d-496d-a652-ed223b542132": {
                            "From": "nodepub2/pubport/out",
                            "To": "nodesub1/subport/in",
                        },
                    },
                    "NodeInst": {
                        "nodepub1": {
                            "NodeLabel": "NodePub1",
                            "Template": "NodePub1",
                        },
                        "nodepub2": {
                            "NodeLabel": "NodePub2",
                            "Template": "NodePub2",
                        },
                        "nodesub1": {
                            "NodeLabel": "NodeSub1",
                            "Template": "NodeSub1",
                        },
                        "nodesub2": {
                            "NodeLabel": "NodeSub2",
                            "Template": "NodeSub2",
                        },
                    },
                }
            }
        }

        scope = scopes(workspace="global")
        scope.write(node_pub1, scope="Node", ref="NodePub1", version="__UNVERSIONED__")
        scope.write(node_pub2, scope="Node", ref="NodePub2", version="__UNVERSIONED__")
        scope.write(node_sub1, scope="Node", ref="NodeSub1", version="__UNVERSIONED__")
        scope.write(node_sub2, scope="Node", ref="NodeSub2", version="__UNVERSIONED__")
        scope.write(flow, scope="Flow", ref="two_pubs_test", version="__UNVERSIONED__")

        remaps = Flow("two_pubs_test").graph.calc_remaps()
        self.assertEqual(
            remaps,
            {
                "nodesub1/subport/in": {
                    "From": ["nodepub1/pubport/out", "nodepub2/pubport/out"],
                    "To": [
                        "nodesub1/subport/in"
                    ],  # without the fix, "To" would also have "nodesub2/subport/in"
                }
            },
        )
