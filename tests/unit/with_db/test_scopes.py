"""Tests for scopes."""


class TestTranslation:
    def test_translation(self, global_db, metadata_folder):
        from dal.tools.backup import Importer
        from dal.scopes import Translation

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
        from dal.tools.backup import Importer

        tool = Importer(
            metadata_folder_invalid_data,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Translation": ["invalid_po"]}

        tool.run(data)

        captured = capsys.readouterr()
        assert "Invalid PO file format for language pt" in captured.out


class TestAlert:
    def test_alert(self, global_db, metadata_folder):
        """Test alert import and export."""
        from dal.tools.backup import Importer
        from dal.scopes import Alert

        tool = Importer(
            metadata_folder,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Alert": ["delete_me"]}

        tool.run(data)

        alert = Alert("delete_me")

        assert alert.Action == "Random action"
        assert alert.Info == "Random info"
        assert alert.Label == "delete_me"
        assert alert.Title == "Delete Me"
        assert alert.User == "movai@internal"
        assert hasattr(alert, "LastUpdate")
