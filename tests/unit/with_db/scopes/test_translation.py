"""Tests for Translation scope."""


import pytest


class TestTranslation:
    def test_translation(self, global_db, metadata_folder):
        from dal.tools.backup import Importer
        from dal.scopes.translation import Translation

        tool = Importer(
            metadata_folder,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Translation": ["delete_me"]}

        tool.run(data)

        trans = Translation("delete_me")

        assert "pt" in trans.Translations
        assert "fr" in trans.Translations
        assert "Olá mundo." in trans.Translations["pt"].po
        assert "Bonjour le monde." in trans.Translations["fr"].po

    def test_translation_invalid_po(self, global_db, metadata_folder_invalid_data, capsys):
        from dal.tools.backup import Importer, ImportException

        tool = Importer(
            metadata_folder_invalid_data,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Translation": ["invalid_po"]}

        with pytest.raises(
            ImportException,
            match="Failed to import Translation:invalid_po - Invalid PO file format for language pt",
        ):
            tool.run(data)
