"""Tests for the extract_i18n module."""

from pathlib import Path

from dal.tools.extract_i18n import parse_directory

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
