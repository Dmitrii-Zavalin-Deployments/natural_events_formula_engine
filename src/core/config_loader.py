import json
import logging
import os
from jsonschema import SchemaError, ValidationError, validate

logger = logging.getLogger(__name__)

DEFAULT_SCHEMA_PATH = "schema/config_schema.json"


def load_config(
    config_path="config/config.json", schema_path=DEFAULT_SCHEMA_PATH
):
    """
    Load configuration from JSON file and validate against JSON schema.
    Enforces:
      - config file must exist
      - schema file must exist
      - JSON must be valid
      - schema validation passes against schema/config_schema.json
    """
    if not os.path.exists(config_path):
        logger.error(f"Configuration file missing: {config_path}")
        raise FileNotFoundError(
            f"[CONFIG ERROR] Required configuration file not found: {config_path}"
        )

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        raise ValueError(
            f"[CONFIG ERROR] Invalid JSON format in {config_path}: {e}"
        )

    if not os.path.exists(schema_path):
        logger.error(f"Schema file missing: {schema_path}")
        raise FileNotFoundError(
            f"[CONFIG ERROR] Required schema file not found: {schema_path}"
        )

    try:
        with open(schema_path, "r") as sf:
            schema = json.load(sf)
        validate(instance=config, schema=schema)
    except ValidationError as e:
        logger.error(f"Config schema validation failed: {e.message}")
        raise ValueError(
            f"[CONFIG ERROR] Schema validation failed for {config_path}: {e.message}"
        )
    except SchemaError as e:
        logger.error(f"Invalid schema definition in {schema_path}: {e}")
        raise ValueError(f"[CONFIG ERROR] Invalid schema definition: {e}")

    logger.info("Configuration loaded and validated against schema successfully.")
    return config
