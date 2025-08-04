"""Tests for scopes."""
import os
from pathlib import Path

CURR_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
METADATA_FOLDER = CURR_DIR / ".." / "data" / "metadata"


class TestTranslation:
    def test_translation(self, global_db):
        from dal.tools.backup import Importer
        from dal.scopes import Translation

        tool = Importer(
            METADATA_FOLDER,
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
