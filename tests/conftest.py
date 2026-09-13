# tests/conftest.py
import json
import os

import cv2
import numpy as np
import pytest


@pytest.fixture
def temp_environment(tmp_path, monkeypatch):
    """Sets up a complete real filesystem environment for test suites."""
    root_dir = tmp_path
    config_dir = root_dir / "config"
    schema_dir = root_dir / "schema"
    raw_dir = root_dir / "data" / "raw"
    processed_dir = root_dir / "data" / "processed"
    output_dir = root_dir / "data" / "output"

    config_dir.mkdir(parents=True, exist_ok=True)
    schema_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use project schema if present, fallback to schema structure
    schema_source = os.path.join("schema", "config_schema.json")
    if os.path.exists(schema_source):
        with open(schema_source, "r") as sf:
            schema_data = json.load(sf)
    else:
        schema_data = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["dry_run", "measurements"]},
                "paths": {
                    "type": "object",
                    "properties": {
                        "raw_folder": {"type": "string"},
                        "processed_folder": {"type": "string"},
                        "output_csv": {"type": "string"},
                    },
                    "required": ["raw_folder", "processed_folder", "output_csv"],
                },
                "grid": {
                    "type": "object",
                    "properties": {
                        "cell_width_px": {"type": "integer"},
                        "cell_height_px": {"type": "integer"},
                        "grid_thickness": {"type": "integer"},
                        "grid_color": {"type": "string"},
                        "text_color": {"type": "string"},
                    },
                    "required": [
                        "cell_width_px",
                        "cell_height_px",
                        "grid_thickness",
                        "grid_color",
                        "text_color",
                    ],
                },
            },
            "required": ["mode", "paths", "grid"],
        }

    with open(schema_dir / "config_schema.json", "w") as sf:
        json.dump(schema_data, sf)

    # Generate synthetic input image with horizontal line feature
    test_img = np.full((1000, 1000, 3), 200, dtype=np.uint8)
    cv2.line(test_img, (150, 600), (350, 600), (0, 0, 0), 5)
    cv2.imwrite(str(raw_dir / "IMG_20260908_152921.jpg"), test_img)

    monkeypatch.chdir(root_dir)
    return root_dir
