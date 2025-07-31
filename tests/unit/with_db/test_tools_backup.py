"""Tests for backup tool."""
import os
from pathlib import Path
import pytest

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
