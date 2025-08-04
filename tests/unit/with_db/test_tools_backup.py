"""Tests for backup tool."""
import os
from pathlib import Path
from filecmp import cmpfiles

CURR_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
METADATA_FOLDER = CURR_DIR / ".." / "data" / "metadata"
MANIFEST = CURR_DIR / ".." / "data" / "manifest.txt"


class TestToolsBackup:
    def test_import_manifest(self, global_db):
        from dal.tools.backup import Importer

        tool = Importer(
            METADATA_FOLDER,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        objects = tool.read_manifest(MANIFEST)

        tool.run(objects)

    def test_export_manifest(self, global_db, tmp_path):
        from dal.tools.backup import Exporter

        tool = Exporter(
            tmp_path,
            debug=False,
            recursive=False,
        )

        objects = tool.read_manifest(MANIFEST)

        tool.run(objects)

    def test_relative_import(self, global_db):
        from dal.tools.backup import Importer

        METADATA_FOLDER_RELATIVE = METADATA_FOLDER.relative_to(os.getcwd())
        MANIFEST_RELATIVE = MANIFEST.relative_to(os.getcwd())

        tool = Importer(
            METADATA_FOLDER_RELATIVE,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        objects = tool.read_manifest(MANIFEST_RELATIVE)

        tool.run(objects)

    def test_import_export_translation(self, global_db, tmp_path):
        """Test translation import and export."""
        from dal.tools.backup import Importer, Exporter

        importer = Importer(
            METADATA_FOLDER,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Translation": ["delete_me"]}

        importer.run(data)

        exporter = Exporter(
            tmp_path,
            debug=False,
            recursive=False,
        )

        exporter.run(data)

        to_check = [
            "delete_me.json",
            "delete_me_pt.po",
            "delete_me_fr.po",
        ]

        equal, diff, err = cmpfiles(
            METADATA_FOLDER / "Translation", tmp_path / "Translation", to_check
        )
        assert set(equal) == set(to_check)
        assert not diff
        assert not err
