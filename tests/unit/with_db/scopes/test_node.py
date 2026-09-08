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

        assert node.Info == "imported node"
        assert node.Label == "delete_me"
        assert node.User == ""
        assert hasattr(node, "LastUpdate")

    def test_import_forbidden_words(self, global_db, metadata_folder_invalid_data):
        """Test node import with forbidden words."""
        import pytest

        from dal.tools.backup import Importer, ImportException

        tool = Importer(
            metadata_folder_invalid_data,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Node": ["containing_start"]}
        with pytest.raises(
            ImportException,
            match="Aborted import: 'containing_start' is not valid for type Node because it contains 'start'",
        ):
            tool.run(data)

        data = {"Node": ["containing_forbidden_words"]}
        with pytest.raises(
            ImportException,
            match="Aborted import: In containing_forbidden_words, 'a_topic_with_the_word_end' is not valid because it contains 'end'",
        ):
            tool.run(data)
