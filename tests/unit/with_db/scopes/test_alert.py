"""Tests for Alert scope."""


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
