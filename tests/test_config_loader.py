import json

import pytest

from src.core.config_loader import load_config


def test_load_config_success(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    config_data = {"mode": "dry_run", "paths": {}, "grid": {}}
    config_file.write_text(json.dumps(config_data))

    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    schema_file = schema_dir / "config_schema.json"
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

    result = load_config(str(config_file), str(schema_file))
    assert result == config_data


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError, match="Required configuration file not found"):
        load_config("nonexistent_config.json", "nonexistent_schema.json")


def test_load_config_invalid_json(tmp_path):
    config_file = tmp_path / "bad_config.json"
    config_file.write_text("{ invalid json ...")
    
    schema_file = tmp_path / "schema.json"
    schema_file.write_text("{}")

    with pytest.raises(ValueError, match="Invalid JSON format"):
        load_config(str(config_file), str(schema_file))


def test_load_schema_file_not_found(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"mode": "test"}))

    with pytest.raises(FileNotFoundError, match="Required schema file not found"):
        load_config(str(config_file), "nonexistent_schema.json")


def test_load_config_validation_error(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"mode": 123}))  # invalid type, expects string

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

    with pytest.raises(ValueError, match="Schema validation failed"):
        load_config(str(config_file), str(schema_file))


def test_load_config_invalid_schema_definition(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"mode": "test"}))

    schema_file = tmp_path / "bad_schema.json"
    # Malformed schema (type should be string/array, not an integer)
    schema_data = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": 999 
    }
    schema_file.write_text(json.dumps(schema_data))

    with pytest.raises(ValueError, match="Invalid schema definition"):
        load_config(str(config_file), str(schema_file))
