import os
import unittest
import pytest
from unittest.mock import Mock, patch

from dal.models.flow import Flow
from dal.models.scopestree import scopes
from dal.utils.redis_mocks import fake_redis

test_dir = os.path.dirname(__file__)


class FlowTests(unittest.TestCase):
    maxDiff = None

    @pytest.mark.skipif()  # this validation is currently being done in the flow-initiator repository. Future refactor should centralize all flow validations
    @fake_redis("dal.movaidb.redis_clients.Connection", recording_dir=test_dir)
    @fake_redis("dal.plugins.persistence.redis.redis.Connection", recording_dir=test_dir)
    def test_no_remap_two_inports(self):
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

        print(remaps)
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

    @pytest.mark.skipif()
    @fake_redis("dal.movaidb.database.Connection", recording_dir=test_dir)
    @fake_redis("dal.plugins.persistence.redis.redis.Connection", recording_dir=test_dir)
    def test_remap_four_nodes_pub_non_remapable(self):
        node_pub1 = {
            "Node": {
                "Node1Remapable1": {
                    "Info": "First publisher",
                    "Label": "noderemapable1",
                    "LastUpdate": "04/06/2020 at 07:10:28",
                    "PortsInst": {
                        "pub_remapable_port1": {
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
                "Node1NonRemapable1": {
                    "Info": "Second publisher",
                    "Label": "nonremapable1",
                    "LastUpdate": "04/06/2020 at 07:10:28",
                    "PortsInst": {
                        "pub_non_remapable_port1": {
                            "Message": "Float32",
                            "Out": {"out": {"Message": "std_msgs/Float32"}},
                            "Package": "std_msgs",
                            "Template": "ROS1/Publisher",
                        }
                    },
                    "Type": "ROS1/Node",
                    "Remappable": False,
                }
            }
        }

        node_sub1 = {
            "Node": {
                "Node1Remapable2": {
                    "Info": "First subscriber",
                    "Label": "noderemapable2",
                    "LastUpdate": "04/06/2020 at 07:10:28",
                    "PortsInst": {
                        "sub_remapable_port1": {
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
                "Node1Remapable3": {
                    "Info": "Second subscriber",
                    "Label": "noderemapable3",
                    "LastUpdate": "04/06/2020 at 07:10:28",
                    "PortsInst": {
                        "sub_remapable_port2": {
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
                "one_remapable_in_linked_star_remap": {
                    "Description": "test",
                    "ExposedPorts": {
                        "Node1Remapable1": {"noderemapable1": ["pub_remapable_port1/out"]},
                        "Node1NonRemapable1": {"nonremapable1": ["pub_non_remapable_port1/out"]},
                        "Node1Remapable2": {"noderemapable2": ["sub_remapable_port1/in"]},
                        "Node1Remapable3": {"noderemapable3": ["sub_remapable_port2/in"]},
                    },
                    "Label": "one_remapable_in_linked_star_remap",
                    "LastUpdate": "09/10/2020 at 12:24:44",
                    "Links": {
                        "06eed84a-1a7f-4af1-95e1-e1edfc62ea3": {
                            "From": "noderemapable1/pub_remapable_port1/out",
                            "To": "noderemapable2/sub_remapable_port1/in",
                        },
                        "652744ed-63cd-463d-9eba-432fd7f7ea7d": {
                            "From": "noderemapable1/pub_remapable_port1/out",
                            "To": "noderemapable3/sub_remapable_port2/in",
                        },
                        "070ab147-280d-496d-a652-ed223sdfs42132": {
                            "From": "nonremapable1/pub_non_remapable_port1/out",
                            "To": "noderemapable2/sub_remapable_port1/in",
                        },
                        "070ab147-290d-496d-df52-ed223b542465": {
                            "From": "nonremapable1/pub_non_remapable_port1/out",
                            "To": "noderemapable3/sub_remapable_port2/in",
                        },
                    },
                    "NodeInst": {
                        "noderemapable1": {
                            "NodeLabel": "Node1Remapable1",
                            "Template": "Node1Remapable1",
                        },
                        "nonremapable1": {
                            "NodeLabel": "Node1NonRemapable1",
                            "Template": "Node1NonRemapable1",
                        },
                        "noderemapable2": {
                            "NodeLabel": "NodeSub1",
                            "Template": "Node1Remapable2",
                        },
                        "noderemapable3": {
                            "NodeLabel": "NodeSub2",
                            "Template": "Node1Remapable3",
                        },
                    },
                }
            }
        }

        scope = scopes(workspace="global")
        scope.write(node_pub1, scope="Node", ref="Node1Remapable1", version="__UNVERSIONED__")
        scope.write(node_pub2, scope="Node", ref="Node1NonRemapable1", version="__UNVERSIONED__")
        scope.write(node_sub1, scope="Node", ref="Node1Remapable2", version="__UNVERSIONED__")
        scope.write(node_sub2, scope="Node", ref="Node1Remapable3", version="__UNVERSIONED__")
        scope.write(
            flow, scope="Flow", ref="one_remapable_in_linked_star_remap", version="__UNVERSIONED__"
        )

        remaps = Flow("one_remapable_in_linked_star_remap").graph.calc_remaps()

        pub2_name_key = list(node_pub2["Node"].keys())[0]
        pub2_name = node_pub2["Node"][pub2_name_key]["Label"]

        port_pub2_key = list(node_pub2["Node"][pub2_name_key]["PortsInst"].keys())[0]

        self.assertEqual(list(remaps.keys())[0], port_pub2_key)

    @fake_redis("dal.movaidb.redis_clients.Connection", recording_dir=test_dir)
    @fake_redis("dal.plugins.persistence.redis.redis.Connection", recording_dir=test_dir)
    def test_remap_four_nodes_adj_non_remapables(self):
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
                    "Remappable": False,
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
                    "Remappable": False,
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
                        "06eed84a-1a7f-4ad1-95e1-e1dfg8d1c62ea3": {
                            "From": "nodepub1/pubport/out",
                            "To": "nodesub1/subport/in",
                        },
                        "652744ed-63cd-463d-9eba-45bfgddf7ea7d": {
                            "From": "nodepub1/pubport/out",
                            "To": "nodesub2/subport/in",
                        },
                        "070ab147-280d-496d-a652-ed223bdgdf132": {
                            "From": "nodepub2/pubport/out",
                            "To": "nodesub1/subport/in",
                        },
                        "070ab147-290d-496d-a652-ed223bdfgdf2465": {
                            "From": "nodepub2/pubport/out",
                            "To": "nodesub2/subport/in",
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

        with pytest.raises(Exception) as e:
            Flow("two_pubs_test").graph.calc_remaps()

        self.assertEqual(str(e.value), "Flow validation failed. Flow stopped")
        # TODO evaluate the error message

    @pytest.mark.skipif()
    @fake_redis("dal.movaidb.redis_clients.Connection", recording_dir=test_dir)
    @fake_redis("dal.plugins.persistence.redis.redis.Connection", recording_dir=test_dir)
    def test_remap_four_nodes_linked_direct_non_remapable(self):
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
                    "Remappable": False,
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
                    "Remappable": False,
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
                        "070ab147-290d-496d-a652-ed223b542465": {
                            "From": "nodepub2/pubport/out",
                            "To": "nodesub2/subport/in",
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

        with pytest.raises(Exception) as e:
            Flow("two_pubs_test").graph.calc_remaps()
        sub1_name_key = list(node_sub1["Node"].keys())[0]
        pub1_name_key = list(node_pub1["Node"].keys())[0]
        sub1_name = node_sub1["Node"][sub1_name_key]["Label"]
        pub1_name = node_pub1["Node"][pub1_name_key]["Label"]

        port_sub1_key = list(node_sub1["Node"][sub1_name_key]["PortsInst"].keys())[0]

        port_pub1_key = list(node_pub1["Node"][pub1_name_key]["PortsInst"].keys())[0]
        # port_sub1_name = node_sub1["Node"][sub1_name_key]["PortsInst"][port_sub1_key]
        # port_pub1_name = node_pub1["Node"][pub1_name_key]["PortsInst"][port_pub1_key]

        exception_report = str(e.value)
        # self.assertEquals(str(e.value),"Flow validation failed. Flow stopped")
        self.assertIn("Two non remappable nodes are connected: ", exception_report)
        self.assertIn(pub1_name + "/" + port_pub1_key + "/out", exception_report)
        self.assertIn(sub1_name + "/" + port_sub1_key + "/in", exception_report)


class FlowParamsTests(unittest.TestCase):
    @patch("dal.models.scopestree.Persistence.get_plugin_class")
    def test_missing_flow_param(self, mock_get_plugin):
        # Clear existing Redis plugins, if any
        del scopes._children["global"]

        # Set up mocks
        mock_plugin = Mock()
        mock_plugin.return_value = Mock()
        mock_plugin.return_value.read.return_value = Mock()
        mock_plugin.return_value.read.return_value.get.side_effect = [
            "1.0",  # getting schema version
            {
                "test": {
                    "Parameter": {
                        "config_file": {
                            "Value": "$(config project.configurations.smart)",
                            "Description": "",
                            "Type": "any",
                        }
                    }
                }
            },  # getting Flow data
            "1.0",  # getting schema version
            {},  # getting Configuration version
        ]
        mock_get_plugin.return_value = mock_plugin
        flow = Flow("test")

        with self.assertLogs("ParamParser.mov.ai") as cm:
            flow.get_param("config_file")

        self.assertEqual(
            cm.output,
            [
                'ERROR:ParamParser.mov.ai:Error evaluating "config_file" '
                'with value "$(config project.configurations.smart)" of '
                'flow "test"; Configuration project does not exist'
            ],
        )
