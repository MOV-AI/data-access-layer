"""Tests for Node scope."""


class TestNode:
    def test_node(self, global_db, metadata_folder):
        """Test node import and export."""
        from dal.tools.backup import Importer
        from dal.scopes import Node

        tool = Importer(
            metadata_folder,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Node": ["delete_me"]}

        tool.run(data)

        node = Node("delete_me")

        assert node.Info is None
        assert node.Label == "delete_me"
        assert node.User == ""
        assert hasattr(node, "LastUpdate")
