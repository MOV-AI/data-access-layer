"""Tests for the JsonValidator class."""
import pytest
import time

from dal.validation import JsonValidator
import dal.exceptions
from dal.classes.filesystem import FileSystem


@pytest.fixture
def valid_data(metadata_folder):
    data = FileSystem.read_json(metadata_folder / "Translation" / "delete_me.json")
    return data["Translation"]["delete_me"]


@pytest.fixture
def invalid_data(metadata_folder_invalid_data):
    data = FileSystem.read_json(metadata_folder_invalid_data / "Translation" / "delete_me.json")
    return data["Translation"]["delete_me"]


class TestJsonValidator:
    def test_validate(self, valid_data):
        """Test that valid data passes validation."""
        validator = JsonValidator()
        validator.validate("Translation", valid_data)

    def test_validate_negative(self, invalid_data):
        """Test that invalid data fails validation."""
        validator = JsonValidator()
        with pytest.raises(ValueError) as exc_info:
            validator.validate("Translation", invalid_data)
        assert "invalid_data" in str(exc_info.value)

    def test_validate_with_unknown_type(self, valid_data):
        """Test that an unknown type raises SchemaTypeNotKnown."""
        validator = JsonValidator()
        with pytest.raises(dal.exceptions.SchemaTypeNotKnown):
            validator.validate("UnknownType", valid_data)

    def test_validation_performance(self, valid_data):
        """Test that validation does not take too long."""
        validator = JsonValidator()
        start_time = time.perf_counter()
        times = 1000
        for _ in range(times):
            validator.validate("Translation", valid_data)
        time_per_validation = (time.perf_counter() - start_time) / times
        assert time_per_validation < 0.01, "Validation took too long per call"
