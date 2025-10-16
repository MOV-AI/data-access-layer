"""Tests for the Schema class."""
import pytest
from pathlib import Path
import urllib.parse

from dal.validation import Schema
from dal.validation import SCHEMA_FOLDER_PATH
from dal.classes.filesystem import FileSystem


@pytest.fixture
def translation_validator():
    clean_path = urllib.parse.urlparse(SCHEMA_FOLDER_PATH).path
    path = Path(clean_path) / "2.4" / "Translation.schema.json"
    return Schema(path)


@pytest.fixture
def translation_valid_data(metadata_folder):
    data = FileSystem.read_json(metadata_folder / "Translation" / "delete_me.json")
    return data["Translation"]["delete_me"]


@pytest.fixture
def translation_invalid_data(metadata_folder_invalid_data):
    data = FileSystem.read_json(metadata_folder_invalid_data / "Translation" / "delete_me.json")
    return data["Translation"]["delete_me"]


@pytest.fixture
def alert_validator():
    clean_path = urllib.parse.urlparse(SCHEMA_FOLDER_PATH).path
    path = Path(clean_path) / "2.4" / "Alert.schema.json"
    return Schema(path)


@pytest.fixture
def alert_valid_data(metadata_folder):
    data = FileSystem.read_json(metadata_folder / "Alert" / "delete_me.json")
    return data["Alert"]["delete_me"]


@pytest.fixture
def alert_invalid_data(metadata_folder_invalid_data):
    data = FileSystem.read_json(metadata_folder_invalid_data / "Alert" / "delete_me.json")
    return data["Alert"]["delete_me"]


class TestTranslationSchema:
    def test_validate(self, translation_validator, translation_valid_data):
        """Test that valid data passes validation."""
        res = translation_validator.validate(translation_valid_data)
        assert res["status"] is True, res["message"]

    def test_validate_negative(self, translation_validator, translation_invalid_data):
        """Test that invalid data fails validation."""
        res = translation_validator.validate(translation_invalid_data)
        assert res["status"] is False
        assert "invalid_data" in res["message"]


class TestAlertSchema:
    def test_validate(self, alert_validator, alert_valid_data):
        """Test that valid data passes validation."""
        res = alert_validator.validate(alert_valid_data)
        assert res["status"] is True, res["message"]

    def test_validate_negative(self, alert_validator, alert_invalid_data):
        """Test that invalid data fails validation."""
        res = alert_validator.validate(alert_invalid_data)
        assert res["status"] is False
        assert "invalid_data" in res["message"]
