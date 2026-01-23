import sys
from unittest import mock


class TestMobdataCommands:
    def _run_mobdata(self, command, manifest_path: str, metadata_path: str):
        """Helper to run mobdata search command programmatically using main()."""
        from dal.tools.mobdata import main

        # Build command line arguments
        cmd_args = ["mobdata", command, "-i", "-c", "-m", manifest_path, "-p", metadata_path]

        # Mock sys.argv to simulate command-line invocation
        with mock.patch("dal.tools.backup.test_reachable", return_value=True):
            with mock.patch.object(sys, "argv", cmd_args):
                return_code = main()

        return return_code

    def test_import_manifest_command(self, global_db, metadata_folder, manifest_file, capsys):
        return_code = self._run_mobdata("import", str(manifest_file), str(metadata_folder))
        assert return_code == 0
        assert "Imported" in capsys.readouterr().out

        # Check that data has been imported into the database
        from dal.tools.backup import Importer, Factory

        importer = Importer(
            metadata_folder,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )
        expected_objects = importer.read_manifest(manifest_file)
        for expected_scope, expected_names in expected_objects.items():
            scope_class = Factory.get_class(expected_scope)
            existing_names = scope_class.get_all()
            for expected_name in expected_names:
                assert (
                    expected_name in existing_names
                ), f"{expected_scope} {expected_name} should be in DB"

    def test_export_manifest_command(
        self, global_db, metadata_folder, manifest_file, tmp_path, capsys
    ):
        return_code = self._run_mobdata("export", str(manifest_file), str(tmp_path))

        assert return_code == 0
        assert "Exported" in capsys.readouterr().out

        # Verify expected files were exported
        # Read the manifest to know what should be exported
        from dal.tools.backup import Exporter

        exporter = Exporter(tmp_path, debug=False, recursive=False)
        exported_objects = exporter.read_manifest(manifest_file)

        # Check that files exist for each object in manifest
        for expected_scope, exported_names in exported_objects.items():
            scope_dir = tmp_path / expected_scope
            assert scope_dir.exists(), f"{expected_scope} directory should exist"
            for exported_name in exported_names:
                exported_file = scope_dir / f"{exported_name}.json"
                assert (
                    exported_file.exists()
                ), f"{expected_scope}/{exported_name}.json should be exported"

    def test_remove_manifest_command(self, global_db, metadata_folder, manifest_file, capsys):
        from dal.tools.backup import Importer, Factory

        # Import data first to ensure there is something to remove
        self._run_mobdata("import", str(manifest_file), str(metadata_folder))

        return_code = self._run_mobdata("remove", str(manifest_file), str(metadata_folder))
        assert return_code == 0
        assert "Removed" in capsys.readouterr().out

        # Check that data has been removed from the database
        importer = Importer(
            metadata_folder,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )
        removed_objects = importer.read_manifest(manifest_file)
        for expected_scope, removed_names in removed_objects.items():
            scope_class = Factory.get_class(expected_scope)
            all_names = scope_class.get_all()
            for removed_name in removed_names:
                assert (
                    removed_name not in all_names
                ), f"{expected_scope} {removed_name} should be removed from DB"
