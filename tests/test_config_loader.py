# tests/test_config_loader.py
# ==============================================================================
# LITERATE TESTING STANDARD: CONFIGURATION LOADER VERIFICATION
# ==============================================================================
# This module verifies the behavior and error handling of the configuration
# loading subsystem under valid, missing, malformed, and invalid schema states.

import json
import pytest

from src.core.config_loader import load_config


def test_load_config_success(tmp_path):
    """
    Narrative: When a well-formed JSON configuration file and a corresponding
    valid JSON schema are provided, the configuration loader must successfully
    parse and return the dictionary representation of the configuration.
    """
    # We establish isolated temporary directories for configuration and schema files.
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    
    # We define a valid configuration dictionary matching required properties.
    config_data = {"mode": "dry_run", "paths": {}, "grid": {}}
    config_file.write_text(json.dumps(config_data))

    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    schema_file = schema_dir / "config_schema.json"
    
    # We define the companion JSON schema enforcing strict object types and required keys.
    schema_data = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "mode": {"type": "string"},
            "paths": {"type": "object"},
            "grid": {"type": "object"}
        },
        "required": ["mode", "paths", "grid"]
    }
    schema_file.write_text(json.dumps(schema_data))

    # We execute the configuration loader and assert that the returned configuration
    # matches our expected source data dictionary.
    result = load_config(str(config_file), str(schema_file))
    assert result == config_data


def test_load_config_file_not_found():
    """
    Narrative: When an attempt is made to load a configuration file from a path
    that does not exist on the filesystem, the loader must raise a FileNotFoundError.
    """
    # We attempt loading non-existent files and verify the expected exception and error match message.
    with pytest.raises(FileNotFoundError, match="Required configuration file not found"):
        load_config("nonexistent_config.json", "nonexistent_schema.json")


def test_load_config_invalid_json(tmp_path):
    """
    Narrative: When a configuration file contains malformed or syntactically invalid
    JSON text, the loader must catch the parsing error and raise a ValueError.
    """
    # We write syntactically invalid JSON text to the configuration file.
    config_file = tmp_path / "bad_config.json"
    config_file.write_text("{ invalid json ...")
    
    schema_file = tmp_path / "schema.json"
    schema_file.write_text("{}")

    # We assert that parsing corrupt JSON raises a ValueError with an invalid format message.
    with pytest.raises(ValueError, match="Invalid JSON format"):
        load_config(str(config_file), str(schema_file))


def test_load_schema_file_not_found(tmp_path):
    """
    Narrative: When the configuration file exists but the specified schema file
    is missing from disk, the loader must raise a FileNotFoundError.
    """
    # We create a valid configuration file but omit the schema file.
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"mode": "test"}))

    # We assert that a missing schema file triggers a FileNotFoundError.
    with pytest.raises(FileNotFoundError, match="Required schema file not found"):
        load_config(str(config_file), "nonexistent_schema.json")


def test_load_config_validation_error(tmp_path):
    """
    Narrative: When the configuration data violates the type constraints defined
    in the JSON schema (e.g., providing an integer where a string is expected),
    the validation engine must raise a ValueError.
    """
    # We write configuration data containing an invalid type for the 'mode' key.
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"mode": 123}))

    schema_file = tmp_path / "schema.json"
    schema_data = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "mode": {"type": "string"}
        },
        "required": ["mode"]
    }
    schema_file.write_text(json.dumps(schema_data))

    # We assert that schema validation failure raises a ValueError.
    with pytest.raises(ValueError, match="Schema validation failed"):
        load_config(str(config_file), str(schema_file))


def test_load_config_invalid_schema_definition(tmp_path):
    """
    Narrative: When the schema definition itself is malformed or invalid according
    to schema meta-validators, the loader must catch the definition error and raise a ValueError.
    """
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"mode": "test"}))

    schema_file = tmp_path / "bad_schema.json"
    # We provide a malformed schema where the root type is defined as an integer instead of string/object.
    schema_data = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": 999 
    }
    schema_file.write_text(json.dumps(schema_data))

    # We assert that an invalid schema definition raises a ValueError.
    with pytest.raises(ValueError, match="Invalid schema definition"):
        load_config(str(config_file), str(schema_file))
