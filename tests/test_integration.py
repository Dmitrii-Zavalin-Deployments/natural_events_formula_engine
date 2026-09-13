import csv
import json
from unittest.mock import patch

import cv2
import numpy as np

from measure_object import main


def _create_dummy_image(path):
    img = np.zeros((1000, 1000, 3), dtype=np.uint8)
    cv2.rectangle(img, (200, 600), (300, 800), (255, 255, 255), -1)
    cv2.imwrite(str(path), img)


def setup_test_directory(temp_env, mode):
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
    setup_test_directory(temp_environment, "dry_run")
    monkeypatch.chdir(temp_environment)

    with patch("webbrowser.open"):
        main()

    processed_img = temp_environment / "data" / "processed" / "IMG_20260908_152921.jpg"
    assert processed_img.exists()


def test_integration_measure_object_full_measurements(temp_environment, monkeypatch):
    setup_test_directory(temp_environment, "measurements")
    monkeypatch.chdir(temp_environment)

    with patch("webbrowser.open"), patch("builtins.input", return_value="12"):
        main()

    csv_path = temp_environment / "data" / "output" / "measurements.csv"
    assert csv_path.exists()

    with open(csv_path, "r", newline="") as f:
        reader = list(csv.reader(f))
        assert len(reader) >= 2
        assert reader[0] == ["datetime", "cell_number", "x_range", "y_range"]
        assert reader[1][0] == "2026-09-08 15:29:21"
        assert reader[1][1] == "12"
