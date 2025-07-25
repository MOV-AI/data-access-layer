"""Tests for the JsonValidator class."""
import pytest
import time

from dal.validation import JsonValidator
from dal.exceptions import SchemaTypeNotKnown, SchemaVersionError, SchemaLoadError


@pytest.fixture
def valid_data():
    return {
        "Label": "test",
        "LastUpdate": {"user": "N/A", "date": "N/A"},
        "Translations": {"en": "test", "pt": "teste", "es": "prueba"},
    }


@pytest.fixture
def invalid_data():
    return {
        "Label": "test",
        "LastUpdate": {"user": "N/A", "date": "N/A"},
        "Translations": "invalid_data",
    }


class TestJsonValidator:
    def test_validate(self, valid_data):
        """Test that valid data passes validation."""
        validator = JsonValidator("2.4")
        validator.validate("Translation", valid_data)

    def test_validate_negative(self, invalid_data):
        """Test that invalid data fails validation."""
        validator = JsonValidator("2.4")
        with pytest.raises(ValueError) as exc_info:
            validator.validate("Translation", invalid_data)
        assert "invalid_data" in str(exc_info.value)

    def test_validate_with_invalid_version(self, valid_data):
        """Test that an invalid version raises SchemaVersionError."""
        with pytest.raises(SchemaVersionError):
            JsonValidator("2.3")

    def test_validate_with_unknown_type(self, valid_data):
        """Test that an unknown type raises SchemaTypeNotKnown."""
        validator = JsonValidator("2.4")
        with pytest.raises(SchemaTypeNotKnown):
            validator.validate("UnknownType", valid_data)

    def test_validation_performance(self, valid_data):
        """Test that validation does not take too long."""
        validator = JsonValidator("2.4")
        start_time = time.perf_counter()
        times = 1000
        for _ in range(times):
            validator.validate("Translation", valid_data)
        time_per_validation = (time.perf_counter() - start_time) / times
        assert time_per_validation < 0.01, "Validation took too long per call"
