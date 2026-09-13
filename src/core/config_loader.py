import json
import logging
import os

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ["raw_folder", "processed_folder", "output_csv"]


def load_config(config_path="config/config.json"):
    """
    Load configuration from JSON file.
    Enforces:
      - file must exist
      - JSON must be valid
      - required fields must be present
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

    missing = [field for field in REQUIRED_FIELDS if field not in config]
    if missing:
        logger.error(f"Missing required config fields: {missing}")
        raise KeyError(
            f"[CONFIG ERROR] Missing required fields in {config_path}: {missing}"
        )

    logger.info("Configuration loaded successfully.")
    return config

