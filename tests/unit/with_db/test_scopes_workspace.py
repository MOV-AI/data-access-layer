class TestScopeWorkspace:
    def test_unload_all_keep_scopes(self, setup_test_data):
        """Tests that unload_all() keeps the documents of the scopes asked for."""

        from dal.models.scopestree import scopes

        workspace = scopes()
        node_ref = workspace.list_scopes(scope="Node")[0]["ref"]
        flow_ref = workspace.list_scopes(scope="Flow")[0]["ref"]
        node = scopes.from_path(node_ref, scope="Node")
        flow = scopes.from_path(flow_ref, scope="Flow")

        workspace.unload_all(keep_scopes=["Node"])

        assert scopes.from_path(node_ref, scope="Node") is node
        assert scopes.from_path(flow_ref, scope="Flow") is not flow

    def test_loaded_refs(self, setup_test_data):
        """Tests that loaded_refs() lists the documents loaded in the workspace."""

        from dal.models.scopestree import scopes

        workspace = scopes()
        node_ref = workspace.list_scopes(scope="Node")[0]["ref"]
        workspace.unload_all()
        assert node_ref not in workspace.loaded_refs("Node")

        scopes.from_path(node_ref, scope="Node")
        assert node_ref in workspace.loaded_refs("Node")

        workspace.unload(scope="Node", ref=node_ref)
        assert node_ref not in workspace.loaded_refs("Node")
        assert workspace.loaded_refs("NotAScope") == []
