# tests/conftest.py
# ==============================================================================
# LITERATE TESTING STANDARD: TEST ENVIRONMENT FIXTURES
# ==============================================================================
# This module establishes a fully isolated, deterministic filesystem environment
# and shared fixtures for the test suite, ensuring clean test runs without
# side effects on the host file system.

import json
import os

import cv2
import numpy as np
import pytest


@pytest.fixture
def temp_environment(tmp_path, monkeypatch):
    """Sets up a complete real filesystem environment for test suites."""
    
    # We establish the root temporary directory and subdirectories for configuration,
    # JSON schemas, raw inputs, processed outputs, and results.
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

    # We attempt to locate the project configuration schema source; if absent,
    # we generate a fallback schema defining expected validation rules for execution
    # modes, path mappings, and grid parameters.
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
                        "text_size": {"type": "integer"},
                        "text_color": {"type": "string"},
                    },
                    "required": [
                        "cell_width_px",
                        "cell_height_px",
                        "grid_thickness",
                        "grid_color",
                        "text_size",
                        "text_color",
                    ],
                },
            },
            "required": ["mode", "paths", "grid"],
        }

    with open(schema_dir / "config_schema.json", "w") as sf:
        json.dump(schema_data, sf)

    # For visual and grid processing tests, we synthesize a test image of dimension
    # 1000x1000 pixels with a neutral background (pixel intensity 200) and draw a 
    # horizontal line feature with coordinates from (150, 600) to (350, 600) and thickness 5.
    img_height, img_width = 1000, 1000
    test_img = np.full((img_height, img_width, 3), 200, dtype=np.uint8)
    
    pt1 = (150, 600)
    pt2 = (350, 600)
    line_color = (0, 0, 0)
    line_thickness = 5
    cv2.line(test_img, pt1, pt2, line_color, line_thickness)
    
    # We assert that the test image has been correctly instantiated with expected shape.
    assert test_img.shape == (img_height, img_width, 3)

    # We write the synthetic image to the raw data directory using a standardized timestamp format.
    target_img_path = raw_dir / "IMG_20260908_152921.jpg"
    cv2.imwrite(str(target_img_path), test_img)
    assert target_img_path.exists()

    # We redirect the current working directory to the temporary root directory
    # to ensure relative path resolution behaves deterministically.
    monkeypatch.chdir(root_dir)
    return root_dir
