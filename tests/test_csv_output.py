import csv
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from measure_object import main


def test_csv_output_columns_and_values(monkeypatch, tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    processed_dir = tmp_path / "processed"
    output_csv = tmp_path / "measurements.csv"

    # Create a dummy image matching expected timestamp naming convention
    img_path = raw_dir / "IMG_20260913_120000.jpg"
    dummy = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.imwrite(str(img_path), dummy)

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

    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    monkeypatch.setattr("builtins.input", lambda prompt="": "0")
    monkeypatch.setattr("webbrowser.open", lambda url: True)
    
    # Return coordinates (50.0, 50.0) which fall into the first grid cell
    monkeypatch.setattr("measure_object.process_image", lambda *args, **kwargs: (50.0, 50.0))

    main()

    assert output_csv.exists(), "CSV output file was not created."

    with open(output_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        expected_columns = ["datetime", "cell_number", "x_range", "y_range"]
        for col in expected_columns:
            assert col in fieldnames, f"Missing expected column '{col}' in CSV headers."

        rows = list(reader)
        assert len(rows) >= 1, "CSV should contain at least one measurement row."

        row = rows[0]
        # Validate exact correctness of values and ranges for coordinate (50.0, 50.0) in a 100x100 grid
        assert row["datetime"] == "2026-09-13 12:00:00"
        assert row["cell_number"] == "0"
        assert row["x_range"] == "[0,100)"
        assert row["y_range"] == "[0,100)"