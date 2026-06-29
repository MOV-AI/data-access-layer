"""Tests for backup tool."""
import os
import json
from filecmp import cmpfiles

import pytest


class TestToolsBackup:
    """Test suite for the backup tool's import/export functionality.

    This test class covers core scope import/export functions available in data-access-layer:
    - Callback (with .py file import)
    - Configuration (with .yaml file import)
    - Flow (with recursive dependency imports)
    - Node (single and multiple imports)
    - Package (recursive file imports)
    - StateMachine
    - Translation (with .po file import)
    - Alert

    **Note**: Enterprise scopes (Annotation, GraphicScene, Layout, SharedDataEntry, SharedDataTemplate)
    are tested in flow-initiator/tests/unit/with_db/test_enterprise_import_export.py since they require
    movai_core_enterprise which is not available in data-access-layer.

    Additional scope-specific tests validate:
    - Recursive dependency imports (Flow -> Node, Flow -> Subflow)
    - Multiple imports in one operation
    - Export validation and file comparison
    - Manifest file processing
    - Invalid data handling
    """

    @staticmethod
    def get_source(manifest_file, metadata_folder, source_type):
        """Get the appropriate source based on the source_type."""
        from dal.tools.backup import FilesystemProjectSource, InMemoryProjectSource

        if source_type == "FilesystemProjectSource":
            return FilesystemProjectSource(metadata_folder)
        else:
            files = {manifest_file.name: manifest_file.read_bytes()}

            for file in metadata_folder.rglob("*"):
                if file.is_file():
                    path = InMemoryProjectSource.normalize_path(file.relative_to(metadata_folder))
                    if path.startswith("metadata/"):
                        path = path[len("metadata/") :]

                    files[path] = file.read_bytes()

            return InMemoryProjectSource(files)

    @pytest.mark.parametrize(
        "source_type",
        [
            "FilesystemProjectSource",
            "InMemoryProjectSource",
        ],
        ids=["FilesystemProjectSource", "InMemoryProjectSource"],
    )
    def test_import_manifest(self, global_db, metadata_folder, manifest_file, source_type):
        from dal.tools.backup import Importer, Backup

        tool = Importer(
            metadata_folder,
            source=self.get_source(manifest_file, metadata_folder, source_type),
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        objects = (
            tool.read_manifest(manifest_file)
            if source_type == "FilesystemProjectSource"
            else Backup.read_manifest_content(manifest_file.read_text(), tool.get_objs)
        )
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

    @pytest.mark.parametrize(
        "source_type",
        [
            "FilesystemProjectSource",
            "InMemoryProjectSource",
        ],
        ids=["FilesystemProjectSource", "InMemoryProjectSource"],
    )
    def test_import_export_alert(
        self, global_db, metadata_folder, manifest_file, tmp_path, source_type
    ):
        """Test alert import and export."""
        from dal.tools.backup import Importer, Exporter

        importer = Importer(
            metadata_folder,
            self.get_source(manifest_file, metadata_folder, source_type),
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Alert": ["delete_me"]}

        importer.run(data)

        exporter = Exporter(
            tmp_path,
            debug=False,
            recursive=False,
        )

        exporter.run(data)

        imported_file = metadata_folder / "Alert" / "delete_me.json"
        exported_file = tmp_path / "Alert" / "delete_me.json"
        with open(imported_file, "r") as imported, open(exported_file, "r") as exported:
            imported_content = json.load(imported)
            exported_content = json.load(exported)

            assert imported_content == exported_content

    @pytest.mark.parametrize(
        "source_type",
        [
            "FilesystemProjectSource",
            "InMemoryProjectSource",
        ],
        ids=["FilesystemProjectSource", "InMemoryProjectSource"],
    )
    def test_import_export_callback(
        self, global_db, metadata_folder, manifest_file, tmp_path, source_type
    ):
        """Test callback import with .py file and export."""
        from dal.tools.backup import Importer, Exporter
        from dal.scopes.callback import Callback

        # Import
        importer = Importer(
            metadata_folder,
            source=self.get_source(manifest_file, metadata_folder, source_type),
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Callback": ["delete_me"]}
        importer.run(data)

        # Validate imported data
        callback = Callback("delete_me")
        assert callback.Label == "delete_me"
        assert callback.Code == 'print("hi")\n'

        # Export
        exporter = Exporter(
            tmp_path,
            debug=False,
            recursive=False,
        )
        exporter.run(data)

        # Validate files exist
        assert (tmp_path / "Callback" / "delete_me.py").exists()
        assert (tmp_path / "Callback" / "delete_me.json").exists()

        # Validate code content matches
        with open(metadata_folder / "Callback" / "delete_me.py", "r") as original_code, open(
            tmp_path / "Callback" / "delete_me.py", "r"
        ) as exported_code:
            assert original_code.read() == exported_code.read()

        # Validate JSON structure
        with open(metadata_folder / "Callback" / "delete_me.json", "r") as original_json, open(
            tmp_path / "Callback" / "delete_me.json", "r"
        ) as callback_json:
            original_content = json.load(original_json)
            exported_content = json.load(callback_json)
            assert original_content == exported_content

    @pytest.mark.parametrize(
        "source_type",
        [
            "FilesystemProjectSource",
            "InMemoryProjectSource",
        ],
        ids=["FilesystemProjectSource", "InMemoryProjectSource"],
    )
    def test_import_export_configuration(
        self, global_db, metadata_folder, manifest_file, tmp_path, source_type
    ):
        """Test configuration import with .yaml file and export."""
        from dal.tools.backup import Importer, Exporter
        from dal.scopes.configuration import Configuration

        # Import
        importer = Importer(
            metadata_folder,
            source=self.get_source(manifest_file, metadata_folder, source_type),
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Configuration": ["delete_me"]}
        importer.run(data)

        # Validate imported data
        config = Configuration("delete_me")
        assert config.Label == "delete_me"
        assert config.Yaml == "key: value\n"

        # Export
        exporter = Exporter(
            tmp_path,
            debug=False,
            recursive=False,
        )
        exporter.run(data)

        # Validate files exist
        assert (tmp_path / "Configuration" / "delete_me.yaml").exists()
        assert (tmp_path / "Configuration" / "delete_me.json").exists()

        # Validate YAML content matches
        with open(metadata_folder / "Configuration" / "delete_me.yaml", "r") as original_yaml, open(
            tmp_path / "Configuration" / "delete_me.yaml", "r"
        ) as exported_yaml:
            assert original_yaml.read() == exported_yaml.read()

        # Validate JSON structure
        with open(metadata_folder / "Configuration" / "delete_me.json", "r") as original_json, open(
            tmp_path / "Configuration" / "delete_me.json", "r"
        ) as exported_json:
            original_content = json.load(original_json)
            exported_content = json.load(exported_json)
            assert original_content == exported_content

    @pytest.mark.parametrize(
        "source_type",
        [
            "FilesystemProjectSource",
            "InMemoryProjectSource",
        ],
        ids=["FilesystemProjectSource", "InMemoryProjectSource"],
    )
    def test_import_export_flow(
        self, global_db, metadata_folder, manifest_file, tmp_path, source_type
    ):
        """Test flow import and export."""
        from dal.tools.backup import Importer, Exporter
        from dal.scopes.flow import Flow

        # Import
        importer = Importer(
            metadata_folder,
            source=self.get_source(manifest_file, metadata_folder, source_type),
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Flow": ["delete_me"]}
        importer.run(data)

        # Validate imported data
        flow = Flow("delete_me")
        assert flow.Label == "delete_me"
        assert flow.Description == "imported flow"
        assert flow.ExposedPorts == {}
        assert "delete_me" in flow.NodeInst

        # Export
        exporter = Exporter(
            tmp_path,
            debug=False,
            recursive=False,
        )
        exporter.run(data)

        # Compare files
        imported_file = metadata_folder / "Flow" / "delete_me.json"
        exported_file = tmp_path / "Flow" / "delete_me.json"
        with open(imported_file, "r") as imported, open(exported_file, "r") as exported:
            imported_content = json.load(imported)
            exported_content = json.load(exported)
            assert imported_content == exported_content

    @pytest.mark.parametrize(
        "source_type",
        [
            "FilesystemProjectSource",
            "InMemoryProjectSource",
        ],
        ids=["FilesystemProjectSource", "InMemoryProjectSource"],
    )
    def test_import_flow_with_dependencies(
        self, global_db, metadata_folder, manifest_file, tmp_path, source_type
    ):
        """Test flow import with recursive dependencies (nodes and subflows)."""
        from dal.tools.backup import Importer
        from dal.scopes.flow import Flow
        from dal.scopes.node import Node

        # Import with recursive=True to import dependencies
        importer = Importer(
            metadata_folder,
            source=self.get_source(manifest_file, metadata_folder, source_type),
            force=True,
            dry=False,
            debug=False,
            recursive=True,
            clean_old_data=True,
        )

        data = {"Flow": ["flow_with_nodes_and_subflow"]}
        importer.run(data)

        # Validate main flow imported
        flow = Flow("flow_with_nodes_and_subflow")
        assert flow.Label == "flow_with_nodes_and_subflow"
        assert "pub" in flow.NodeInst
        assert "sub" in flow.NodeInst
        assert "subflow" in flow.Container

        # Validate node dependencies were imported
        node_pub1 = Node("NodePub1")
        assert node_pub1.Label == "NodePub1"

        node_sub1 = Node("NodeSub1")
        assert node_sub1.Label == "NodeSub1"

        # Validate subflow dependency was imported
        subflow = Flow("flow_with_duplicated_subflow")
        assert subflow.Label == "flow_with_duplicated_subflow"

    @pytest.mark.parametrize(
        "source_type",
        [
            "FilesystemProjectSource",
            "InMemoryProjectSource",
        ],
        ids=["FilesystemProjectSource", "InMemoryProjectSource"],
    )
    def test_import_export_node(
        self, global_db, metadata_folder, manifest_file, tmp_path, source_type
    ):
        """Test node import and export."""
        from dal.tools.backup import Importer, Exporter
        from dal.scopes.node import Node

        # Import
        importer = Importer(
            metadata_folder,
            source=self.get_source(manifest_file, metadata_folder, source_type),
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Node": ["delete_me"]}
        importer.run(data)

        # Validate imported data
        node = Node("delete_me")
        assert node.Label == "delete_me"
        assert node.Info == "imported node"
        assert "in" in node.PortsInst

        # Export
        exporter = Exporter(
            tmp_path,
            debug=False,
            recursive=False,
        )
        exporter.run(data)

        # Compare files
        imported_file = metadata_folder / "Node" / "delete_me.json"
        exported_file = tmp_path / "Node" / "delete_me.json"
        with open(imported_file, "r") as imported, open(exported_file, "r") as exported:
            imported_content = json.load(imported)
            exported_content = json.load(exported)
            assert imported_content == exported_content

    @pytest.mark.parametrize(
        "source_type",
        [
            "FilesystemProjectSource",
            "InMemoryProjectSource",
        ],
        ids=["FilesystemProjectSource", "InMemoryProjectSource"],
    )
    def test_import_node_multiple(
        self, global_db, metadata_folder, manifest_file, tmp_path, source_type
    ):
        """Test importing multiple nodes at once."""
        from dal.tools.backup import Importer
        from dal.scopes.node import Node

        # Import
        importer = Importer(
            metadata_folder,
            source=self.get_source(manifest_file, metadata_folder, source_type),
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Node": ["NodePub1", "NodePub2", "NodeSub1", "NodeSub2", "UnusedNode"]}
        importer.run(data)

        # Validate all nodes imported
        for node_name in ["NodePub1", "NodePub2", "NodeSub1", "NodeSub2", "UnusedNode"]:
            node = Node(node_name)
            assert node.Label == node_name

    @pytest.mark.parametrize(
        "source_type",
        [
            "FilesystemProjectSource",
            "InMemoryProjectSource",
        ],
        ids=["FilesystemProjectSource", "InMemoryProjectSource"],
    )
    def test_import_package(
        self, global_db, metadata_folder, metadata2_folder, manifest_file, source_type
    ):
        """Test that consecutive imports merge package contents correctly."""
        from dal.tools.backup import Importer
        from dal.scopes.package import Package

        # Clean any existing Package data from previous test runs
        # (clean_old_data doesn't work for Package due to SKIP_SCOPE_DELETE)
        global_db.delete_by_args("Package", Name="maps")

        importer1 = Importer(
            metadata_folder,
            source=self.get_source(manifest_file, metadata_folder, source_type),
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        importer2 = Importer(
            metadata2_folder,
            source=self.get_source(manifest_file, metadata2_folder, source_type),
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        # import delete_me
        data = {"Package": ["maps"]}
        importer1.run(data)
        maps = Package("maps")
        assert set(maps.File.keys()) == {"delete_me.png", "delete_me.yaml"}

        # import delete_me2
        importer2.run(data)
        assert set(maps.File.keys()) == {
            "delete_me.png",
            "delete_me.yaml",
            "delete_me2.png",
            "delete_me2.yaml",
        }

    @pytest.mark.parametrize(
        "source_type",
        [
            "FilesystemProjectSource",
            "InMemoryProjectSource",
        ],
        ids=["FilesystemProjectSource", "InMemoryProjectSource"],
    )
    def test_import_export_translation(
        self, global_db, metadata_folder, manifest_file, tmp_path, source_type
    ):
        """Test translation import and export."""
        from dal.tools.backup import Importer, Exporter

        importer = Importer(
            metadata_folder,
            source=self.get_source(manifest_file, metadata_folder, source_type),
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
            "delete_me.pt.po",
            "delete_me.fr.po",
        ]

        equal, diff, err = cmpfiles(
            metadata_folder / "Translation", tmp_path / "Translation", to_check
        )
        assert set(equal) == set(to_check)
        assert not diff
        assert not err

    @pytest.mark.parametrize(
        "source_type",
        [
            "FilesystemProjectSource",
            "InMemoryProjectSource",
        ],
        ids=["FilesystemProjectSource", "InMemoryProjectSource"],
    )
    def test_import_invalid_data(
        self,
        global_db,
        metadata_folder_invalid_data,
        manifest_file_invalid_data,
        capsys,
        source_type,
    ):
        """Test import validates and reports invalid data."""
        from dal.tools.backup import Importer

        tool = Importer(
            metadata_folder_invalid_data,
            source=self.get_source(
                manifest_file_invalid_data, metadata_folder_invalid_data, source_type
            ),
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
