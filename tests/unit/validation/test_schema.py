"""Tests for the Schema class."""
import pytest
from pathlib import Path
import urllib.parse

from dal.validation import Schema
from dal.validation import SCHEMA_FOLDER_PATH
from dal.classes.filesystem import FileSystem


@pytest.fixture
def validator():
    clean_path = urllib.parse.urlparse(SCHEMA_FOLDER_PATH).path
    path = Path(clean_path) / "2.4" / "Translation.schema.json"
    return Schema(path)


@pytest.fixture
def valid_data(metadata_folder):
    data = FileSystem.read_json(metadata_folder / "Translation" / "delete_me.json")
    return data["Translation"]["delete_me"]


@pytest.fixture
def invalid_data(metadata_folder_invalid_data):
    data = FileSystem.read_json(metadata_folder_invalid_data / "Translation" / "delete_me.json")
    return data["Translation"]["delete_me"]


class TestSchema:
    def test_validate(self, validator, valid_data):
        """Test that valid data passes validation."""
        res = validator.validate(valid_data)
        assert res["status"] is True, res["message"]

    def test_validate_negative(self, validator, invalid_data):
        """Test that invalid data fails validation."""
        res = validator.validate(invalid_data)
        assert res["status"] is False
        assert "invalid_data" in res["message"]
