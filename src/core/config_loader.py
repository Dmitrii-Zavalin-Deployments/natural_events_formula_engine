import json
import logging
import os

from jsonschema import SchemaError, ValidationError, validate

logger = logging.getLogger(__name__)
DEFAULT_SCHEMA_PATH = "schema/config_schema.json"


def load_config(config_path="config/config.json", schema_path=DEFAULT_SCHEMA_PATH):
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
        loc = "->".join(str(p) for p in e.path) if e.path else "root"
        err_msg = f"Validation failed at [{loc}]: {e.message}"
        logger.error(f"Config schema validation failed: {err_msg}")
        raise ValueError(
            f"[CONFIG ERROR] Schema validation failed for {config_path}: {err_msg}"
        )
    except SchemaError as e:
        logger.error(f"Invalid schema definition in schema file: {e}")
        raise ValueError(f"[CONFIG ERROR] Invalid schema definition: {e}")

    logger.info("Configuration loaded and validated against schema successfully.")
    return config
