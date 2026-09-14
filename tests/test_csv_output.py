# tests/test_csv_output.py
# ==============================================================================
# LITERATE TESTING STANDARD: CSV OUTPUT VERIFICATION
# ==============================================================================
# This test suite validates that the measurement processing pipeline correctly
# writes CSV metadata, headers, and computed spatial indices for analyzed images.

import csv
import os
import sys

import cv2
import numpy as np
import pytest

# We insert the source directory into system paths to enable module resolution.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from measure_object import main


def test_csv_output_columns_and_values(monkeypatch, tmp_path):
    """
    Narrative: Given a raw input image with a standard timestamp filename,
    a configured grid resolution, and a mock coordinate measurement, the application
    must process the image and output a correctly structured CSV file containing
    expected headers and deterministic range calculations.
    """
    # We establish isolated temporary directories for raw inputs and outputs.
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    processed_dir = tmp_path / "processed"
    output_csv = tmp_path / "measurements.csv"

    # We create a dummy image matching the expected timestamp naming convention:
    # IMG_YYYYMMDD_HHMMSS.jpg
    img_path = raw_dir / "IMG_20260913_120000.jpg"
    dummy = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.imwrite(str(img_path), dummy)
    assert img_path.exists()

    # We define configuration parameters specifying 100x100 pixel grid cells.
    config_data = {
        "mode": "measurements",
        "paths": {
            "raw_folder": str(raw_dir),
            "processed_folder": str(processed_dir),
            "output_csv": str(output_csv)
        },
        "grid": {
            "cell_width_px": 100,
            "cell_height_px": 100,
            "grid_thickness": 1,
            "grid_color": "#000000",
            "text_color": "#ffffff"
        }
    }

    # We patch configuration loading, user input prompts, browser actions,
    # and image processing coordinates to simulate a deterministic user session.
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    monkeypatch.setattr("builtins.input", lambda prompt="": "0")
    monkeypatch.setattr("webbrowser.open", lambda url: True)

    # For a coordinate of (50.0, 50.0) within 100x100 cells, the expected cell index is 0
    # and the range falls within the interval [0, 100).
    test_coords = (50.0, 50.0)
    monkeypatch.setattr("measure_object.process_image", lambda *args, **kwargs: test_coords)

    # We execute the main measurement routine.
    main()

    # We verify that the output CSV file was successfully generated.
    assert output_csv.exists(), "CSV output file was not created."

    # We open and read the CSV contents to validate headers and row data.
    with open(output_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        # We assert that all required columns are present in the CSV headers.
        expected_columns = ["datetime", "cell_number", "x_range", "y_range"]
        for col in expected_columns:
            assert col in fieldnames, f"Missing expected column '{col}' in CSV headers."

        rows = list(reader)
        assert len(rows) >= 1, "CSV should contain at least one measurement row."

        # We inspect the first record to verify computed numerical and categorical values.
        row = rows[0]
        
        # The extracted datetime is derived from the filename timestamp "20260913_120000".
        expected_datetime = "2026-09-13 12:00:00"
        assert row["datetime"] == expected_datetime

        # For coordinate (50.0, 50.0) in a 100px grid, cell number is 0 and ranges are [0,100).
        assert row["cell_number"] == "0"
        assert row["x_range"] == "[0,100)"
        assert row["y_range"] == "[0,100)"
