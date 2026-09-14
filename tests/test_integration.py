# tests/test_integration.py
# ==============================================================================
# LITERATE TESTING STANDARD: INTEGRATION TEST SUITE
# ==============================================================================
# This module verifies end-to-end integration workflows of the Natural Events
# Formula Engine across dry-run mode and full measurement mode with CSV persistence.

import os
import sys

# We inject the source directory path to enable internal package resolution.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import csv
import json
from unittest.mock import patch

import cv2
import numpy as np

from measure_object import main


def _create_dummy_image(path):
    """
    Narrative: We synthesize a 1000x1000 pixel black image and draw a white
    rectangular feature to simulate visual objects for integration testing.
    """
    img_size = 1000
    img = np.zeros((img_size, img_size, 3), dtype=np.uint8)
    
    # We draw a filled rectangle representing a target measurement object.
    cv2.rectangle(img, (200, 600), (300, 800), (255, 255, 255), -1)
    cv2.imwrite(str(path), img)
    assert path.exists()


def setup_test_directory(temp_env, mode):
    """
    Narrative: We provision configuration files, schema files, and raw data
    directories tailored to the specified operational execution mode ('dry_run' or 'measurements').
    """
    config_content = {
        "mode": mode,
        "paths": {
            "raw_folder": "data/raw",
            "processed_folder": "data/processed",
            "output_csv": "data/output/measurements.csv",
        },
        "grid": {
            "cell_width_px": 250,
            "cell_height_px": 100,
            "grid_thickness": 2,
            "grid_color": "#00FFFF",
            "text_color": "#000000",
            "text_size": 12,
        },
    }
    
    config_dir = temp_env / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    with open(config_dir / "config.json", "w") as cf:
        json.dump(config_content, cf)

    schema_dir = temp_env / "schema"
    schema_dir.mkdir(parents=True, exist_ok=True)
    schema_content = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "mode": {"type": "string"},
            "paths": {"type": "object"},
            "grid": {"type": "object"}
        },
        "required": ["mode", "paths", "grid"]
    }
    with open(schema_dir / "config_schema.json", "w") as sf:
        json.dump(schema_content, sf)

    raw_dir = temp_env / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    _create_dummy_image(raw_dir / "IMG_20260908_152921.jpg")


def test_integration_measure_object_dry_run(temp_environment, monkeypatch):
    """
    Narrative: In 'dry_run' mode, the pipeline must process raw images, apply grid overlays,
    and save the processed image to the designated folder without requiring user input or writing CSV logs.
    """
    setup_test_directory(temp_environment, "dry_run")
    monkeypatch.chdir(temp_environment)

    # We mock web browser interaction to prevent GUI blocking during execution.
    with patch("webbrowser.open"):
        main()

    # We assert that the processed output image exists on disk.
    processed_img = temp_environment / "data" / "processed" / "IMG_20260908_152921.jpg"
    assert processed_img.exists()


def test_integration_measure_object_full_measurements(temp_environment, monkeypatch):
    """
    Narrative: In 'measurements' mode, the pipeline must process raw images, accept interactive
    cell selection inputs, and log structured measurement records with correct headers and timestamps into a CSV file.
    """
    setup_test_directory(temp_environment, "measurements")
    monkeypatch.chdir(temp_environment)

    # We mock browser opening and provide a pre-programmed cell input ('12') for automated execution.
    with patch("webbrowser.open"), patch("builtins.input", return_value="12"):
        main()

    # We verify that the output CSV file has been successfully created.
    csv_path = temp_environment / "data" / "output" / "measurements.csv"
    assert csv_path.exists()

    # We open and read the CSV file to validate header structure and measurement rows.
    with open(csv_path, "r", newline="") as f:
        reader = list(csv.reader(f))
        
        # The CSV must contain at least a header row and one data row.
        assert len(reader) >= 2
        
        # We assert that column headers match the expected schema.
        expected_headers = ["datetime", "cell_number", "x_range", "y_range"]
        assert reader[0] == expected_headers

        # We verify the correctness of the recorded timestamp and selected cell number.
        expected_datetime = "2026-09-08 15:29:21"
        expected_cell = "12"
        
        assert reader[1][0] == expected_datetime
        assert reader[1][1] == expected_cell
