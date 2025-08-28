"""Tests for the extract_i18n module."""

from pathlib import Path
import unittest.mock
from dataclasses import dataclass
from typing import List

from dal.tools.extract_i18n import parse_directory
from dal.tools.extract_i18n import main

DATA_PATH = Path(__file__).parent / "data"


class TestExtractI18n:
    def test_f_string(self, tmp_path):
        with open(tmp_path / "test.py", "w") as f:
            f.write(
                """
s="reason"
logger.info(f'Work conditions not met: {s}', ui=True)
"""
            )

        strings = parse_directory(tmp_path)
        assert len(strings) == 1
        assert strings[0].lineno == 3
        assert strings[0].filename == str(tmp_path / "test.py")
        assert strings[0].is_f_string is True
        assert strings[0].value == "Work conditions not met: {s}"

    def test_parametrized_string(self, tmp_path):
        with open(tmp_path / "test.py", "w") as f:
            f.write(
                """
s="reason"
logger.info('Work conditions not met: %s', s, ui=True)
"""
            )

        strings = parse_directory(tmp_path)
        assert len(strings) == 1
        assert strings[0].lineno == 3
        assert strings[0].filename == str(tmp_path / "test.py")
        assert strings[0].is_f_string is False
        assert strings[0].value == "Work conditions not met: %s"

    def test_long_log_msg(self, tmp_path):
        with open(tmp_path / "test.py", "w") as f:
            f.write(
                """
if ((len(possible_goals) == 0) or (last_goal not in possible_goals)):
    logger.error('Bad use of pick next slot! Node must be used after scan_pickup or scan_drop only.', ui=True, action="Check workflow design")
    gd.oport['none'].send()
"""
            )

        strings = parse_directory(tmp_path)
        assert len(strings) == 1
        assert strings[0].lineno == 3
        assert strings[0].filename == str(tmp_path / "test.py")
        assert strings[0].is_f_string is False
        assert (
            strings[0].value
            == "Bad use of pick next slot! Node must be used after scan_pickup or scan_drop only."
        )

    def test_gen_and_import(self, tmp_path, global_db):
        """Complete test for generating and importing translations."""

        with open(tmp_path / "test.py", "w") as f:
            f.write(
                """
s="reason"
logger.info(f'Work conditions not met: {s}', ui=True)
"""
            )

        main

        @dataclass
        class Args:
            dir: List[str]
            output_path: str
            name: str

        args = Args(dir=[(str(tmp_path),)], output_path=tmp_path, name="test")

        with unittest.mock.patch("argparse.ArgumentParser.parse_args", return_value=args):
            main()

        from dal.tools.backup import Importer
        from dal.scopes import Translation

        importer = Importer(
            tmp_path,
            force=True,
            dry=False,
            debug=False,
            recursive=False,
            clean_old_data=True,
        )

        data = {"Translation": ["test"]}

        importer.run(data)

        trans = Translation("test")

        assert "pt" in trans.Translations
        assert "Work conditions not met" in trans.Translations["pt"].po
