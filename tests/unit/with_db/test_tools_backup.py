"""Tests for backup tool."""
import os
from filecmp import cmpfiles


class TestToolsBackup:
    def test_import_manifest(self, global_db, metadata_folder, manifest_file):
        from dal.tools.backup import Importer

        tool = Importer(
            metadata_folder,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        objects = tool.read_manifest(manifest_file)

        tool.run(objects)

    def test_export_manifest(self, global_db, manifest_file, tmp_path):
        from dal.tools.backup import Exporter

        tool = Exporter(
            tmp_path,
            debug=False,
            recursive=False,
        )

        objects = tool.read_manifest(manifest_file)

        tool.run(objects)

    def test_relative_import(self, global_db, metadata_folder, manifest_file):
        from dal.tools.backup import Importer

        METADATA_FOLDER_RELATIVE = metadata_folder.relative_to(os.getcwd())
        MANIFEST_RELATIVE = manifest_file.relative_to(os.getcwd())

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

    def test_import_export_translation(self, global_db, metadata_folder, manifest_file, tmp_path):
        """Test translation import and export."""
        from dal.tools.backup import Importer, Exporter

        importer = Importer(
            metadata_folder,
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
            metadata_folder / "Translation", tmp_path / "Translation", to_check
        )
        assert set(equal) == set(to_check)
        assert not diff
        assert not err

    def test_import_invalid_data(
        self, global_db, metadata_folder_invalid_data, manifest_file_invalid_data, capsys
    ):
        """Test import validates and reports invalid data."""
        from dal.tools.backup import Importer

        tool = Importer(
            metadata_folder_invalid_data,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        objects = tool.read_manifest(manifest_file_invalid_data)

        tool.run(objects)

        captured = capsys.readouterr()
        assert (
            "Failed to import Translation:delete_me - Invalid data for scope Translation"
            in captured.out
        )
