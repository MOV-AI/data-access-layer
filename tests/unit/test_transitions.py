from functools import partial
import unittest
from unittest.mock import MagicMock, patch
from dal.models.flow import Flow
from dal.models.flowlinks import FlowLinks

# pylint: disable=not-callable


class TestFlowGetNodeDependencies(unittest.TestCase):
    def setUp(self):
        # We essentially create a mock flow object, with false data,
        # but the methods are real, so we can test the logic
        self.flow = MagicMock(name="MockedFlow")
        self.flow.__START__ = "START/START/START"
        self.flow.__END__ = "END/END/END"
        self.flow.workspace = "global"
        self.flow.Container = {}
        # The 'partial' means that we are binding the mock flow as the 'self' argument
        self.flow.get_node_dependencies = partial(Flow.get_node_dependencies, self.flow)
        self.flow.get_node_transitions = partial(Flow.get_node_transitions, self.flow)
        self.flow.get_node_inst = partial(Flow.get_node_inst, self.flow)
        self.flow._with_prefix = partial(Flow._with_prefix, self.flow)

        nodeinst = MagicMock()
        nodeinst.node_template.get_port.return_value.is_transition.return_value = False
        nodeinst.is_state = False

        # Mock attributes required for the test
        self.flow.NodeInst = {
            "NodeA": nodeinst,
            "NodeB": nodeinst,
            "NodeC": nodeinst,
        }
        self.flow.Links = FlowLinks("Links", {})
        self.flow.Links._parent = self.flow
        self.flow.full = Flow.get_dict(self.flow)

    @patch("dal.models.flow.scopes.from_path")
    def test_get_node_dependencies_no_dependencies(self, mock_scopes):
        mock_scopes.return_value = self.flow

        # Test with a node that has no dependencies
        dependencies = self.flow.get_node_dependencies("NodeA")
        self.assertEqual(dependencies, [])

    @patch("dal.models.flow.scopes.from_path")
    def test_get_node_dependencies_with_dependencies(self, mock_scopes):
        mock_scopes.return_value = self.flow

        # Create links with dependencies
        self.flow.Links.add(
            source_node="NodeA",
            source_port="port1",
            target_node="NodeB",
            target_port="port2",
            source_type="out",
            target_type="in",
        )
        self.flow.Links.add(
            source_node="NodeC",
            source_port="port3",
            target_node="NodeA",
            target_port="port4",
            source_type="in",
            target_type="out",
        )
        self.assertEqual(self.flow.Links.count(), 2)
        self.flow.full = Flow.get_dict(self.flow)

        # Test with a node that has dependencies
        dependencies = self.flow.get_node_dependencies("NodeA")
        self.assertEqual(set(dependencies), {"NodeB", "NodeC"})

    @patch("dal.models.flow.scopes.from_path")
    def test_get_node_dependencies_skip_recursion(self, mock_scopes):
        mock_scopes.return_value = self.flow

        # Create links with circular dependencies including an extra node
        self.flow.Links.add(
            source_node="NodeA",
            source_port="port1",
            target_node="NodeB",
            target_port="port2",
            source_type="out",
            target_type="in",
        )
        self.flow.Links.add(
            source_node="NodeB",
            source_port="port3",
            target_node="NodeC",
            target_port="port4",
            source_type="in",
            target_type="out",
        )
        self.flow.Links.add(
            source_node="NodeC",
            source_port="port5",
            target_node="NodeA",
            target_port="port6",
            source_type="out",
            target_type="in",
        )
        self.assertEqual(self.flow.Links.count(), 3)
        self.flow.full = Flow.get_dict(self.flow)

        dependencies = self.flow.get_node_dependencies("NodeA")
        self.assertEqual(set(dependencies), {"NodeB", "NodeC"})

    @patch("dal.models.flow.scopes.from_path")
    def test_get_node_dependencies_first_level_only(self, mock_scopes):
        mock_scopes.return_value = self.flow

        # Create links with multiple levels of dependencies
        self.flow.Links.add(
            source_node="NodeA",
            source_port="port1",
            target_node="NodeB",
            target_port="port2",
            source_type="out",
            target_type="in",
        )
        self.flow.Links.add(
            source_node="NodeB",
            source_port="port3",
            target_node="NodeC",
            target_port="port4",
            source_type="in",
            target_type="out",
        )
        self.assertEqual(self.flow.Links.count(), 2)
        self.flow.full = Flow.get_dict(self.flow)

        dependencies = self.flow.get_node_dependencies("NodeA", first_level_only=True)
        self.assertEqual(set(dependencies), {"NodeB"})


class TestFlowGetNodeTransitions(unittest.TestCase):
    def setUp(self):
        # We essentially create a mock flow object, with false data,
        # but the methods are real, so we can test the logic
        self.flow = MagicMock(name="MockedFlow")
        self.flow.__START__ = "START/START/START"
        self.flow.__END__ = "END/END/END"
        self.flow.workspace = "global"
        self.flow.Container = {}
        # The 'partial' means that we are binding the mock flow as the 'self' argument
        self.flow.get_node_dependencies = partial(Flow.get_node_dependencies, self.flow)
        self.flow.get_node_transitions = partial(Flow.get_node_transitions, self.flow)
        self.flow.get_node_inst = partial(Flow.get_node_inst, self.flow)
        self.flow._with_prefix = partial(Flow._with_prefix, self.flow)

        nodeinst = MagicMock()
        nodeinst.node_template.get_port.return_value.is_transition.return_value = True
        nodeinst.is_state = False

        # Mock attributes required for the test
        self.flow.NodeInst = {
            "NodeA": nodeinst,
            "NodeB": nodeinst,
            "NodeC": nodeinst,
        }
        self.flow.Links = FlowLinks("Links", {})
        self.flow.Links._parent = self.flow
        self.flow.full = Flow.get_dict(self.flow)

    @patch("dal.models.flow.scopes.from_path")
    def test_get_node_transitions_no_transitions(self, mock_scopes):
        mock_scopes.return_value = self.flow

        # Test with a node that has no transitions
        transitions = self.flow.get_node_transitions("NodeA")
        self.assertEqual(transitions, set())

    @patch("dal.models.flow.scopes.from_path")
    def test_get_node_transitions_with_transitions(self, mock_scopes):
        mock_scopes.return_value = self.flow

        # Create links with transitions
        self.flow.Links.add(
            source_node="NodeA",
            source_port="port1",
            target_node="NodeB",
            target_port="port2",
            source_type="out",
            target_type="in",
        )
        self.flow.Links.add(
            source_node="NodeA",
            source_port="port3",
            target_node="NodeC",
            target_port="port4",
            source_type="out",
            target_type="in",
        )
        self.assertEqual(self.flow.Links.count(), 2)
        self.flow.full = Flow.get_dict(self.flow)

        # Test with a node that has transitions
        transitions = self.flow.get_node_transitions("NodeA")
        self.assertEqual(transitions, {"NodeB", "NodeC"})

    @patch("dal.models.flow.scopes.from_path")
    def test_get_node_transitions_filtered_by_port(self, mock_scopes):
        mock_scopes.return_value = self.flow

        # Create links with transitions
        self.flow.Links.add(
            source_node="NodeA",
            source_port="port1",
            target_node="NodeB",
            target_port="port2",
            source_type="out",
            target_type="in",
        )
        self.flow.Links.add(
            source_node="NodeA",
            source_port="port3",
            target_node="NodeC",
            target_port="port4",
            source_type="out",
            target_type="in",
        )
        self.assertEqual(self.flow.Links.count(), 2)
        self.flow.full = Flow.get_dict(self.flow)

        # Test with a node filtered by port name
        transitions = self.flow.get_node_transitions("NodeA", port_name="port1")
        self.assertEqual(transitions, {"NodeB", "NodeC"})

    @patch("dal.models.flow.scopes.from_path")
    def test_get_node_transitions_no_transition_ports(self, mock_scopes):
        mock_scopes.return_value = self.flow

        # Mock NodeInst to return False for is_transition
        self.flow.NodeInst[
            "NodeA"
        ].node_template.get_port.return_value.is_transition.return_value = False

        # Create links
        self.flow.Links.add(
            source_node="NodeA",
            source_port="port1",
            target_node="NodeB",
            target_port="port2",
            source_type="out",
            target_type="in",
        )
        self.assertEqual(self.flow.Links.count(), 1)
        self.flow.full = Flow.get_dict(self.flow)

        # Test with a node that has no transition ports
        transitions = self.flow.get_node_transitions("NodeA")
        self.assertEqual(transitions, set())


if __name__ == "__main__":
    unittest.main()
