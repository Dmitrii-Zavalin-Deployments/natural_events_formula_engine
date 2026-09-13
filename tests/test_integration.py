# tests/test_integration.py
import csv
import json
import os
import subprocess
import sys
from unittest.mock import patch


def test_integration_measure_object_dry_run(temp_environment):
    """Integration test executing measure_object.py in dry_run mode."""
    config_content = {
        "mode": "dry_run",
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
    config_dir = temp_environment / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    with open(config_dir / "config.json", "w") as cf:
        json.dump(config_content, cf)

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    script_path = os.path.join(repo_root, "src", "measure_object.py")

    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(repo_root, "src")
    env["COVERAGE_PROCESS_START"] = os.path.abspath(".coveragerc") if os.path.exists(".coveragerc") else ""

    result = subprocess.run(
        [sys.executable, "-m", "coverage", "run", "--parallel-mode", script_path],
        capture_output=True,
        text=True,
        cwd=temp_environment,
        env=env,
        check=False,
    )

    assert result.returncode == 0, f"Stdout: {result.stdout}\nStderr: {result.stderr}"
    assert "Starting Natural Events Formula Engine measurement run..." in result.stdout
    assert "Found 1 images to process." in result.stdout
    assert "[DRY-RUN] Bypassed GUI/CLI prompt for IMG_20260908_152921.jpg" in result.stdout
    assert "[DRY-RUN] Would process template matching and write to data/output/measurements.csv" in result.stdout
    assert "Measurement run complete." in result.stdout

    processed_img = temp_environment / "data" / "processed" / "IMG_20260908_152921.jpg"
    assert processed_img.exists()


class _MockProc:
    def __init__(self, *args, **kwargs):
        self.args = args[0] if args else []
        self.returncode = 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def communicate(self, input=None, timeout=None):
        return ("", "")

    def poll(self):
        return self.returncode

    def wait(self):
        return self.returncode


@patch("subprocess.Popen", side_effect=lambda *a, **k: _MockProc(*a, **k))
def test_integration_measure_object_full_measurements(mock_popen, temp_environment):
    """Integration test executing measure_object.py in measurements mode."""
    config_content = {
        "mode": "measurements",
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
    config_dir = temp_environment / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    with open(config_dir / "config.json", "w") as cf:
        json.dump(config_content, cf)

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    script_path = os.path.join(repo_root, "src", "measure_object.py")

    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(repo_root, "src")
    env["COVERAGE_PROCESS_START"] = os.path.abspath(".coveragerc") if os.path.exists(".coveragerc") else ""

    result = subprocess.run(
        [sys.executable, "-m", "coverage", "run", "--parallel-mode", script_path],
        input="12\n",
        capture_output=True,
        text=True,
        cwd=temp_environment,
        env=env,
        check=False,
        timeout=15,
    )

    assert result.returncode == 0, f"Stdout: {result.stdout}\nStderr: {result.stderr}"
    assert "Running automatic template-matching measurements & serialization..." in result.stdout
    assert "Measurement run complete." in result.stdout

    csv_path = temp_environment / "data" / "output" / "measurements.csv"
    assert csv_path.exists()

    with open(csv_path, "r", newline="") as f:
        reader = list(csv.reader(f))
        assert len(reader) >= 2
        assert reader[0] == ["datetime", "cell_number", "x_range", "y_range"]
        assert reader[1][0] == "2026-09-08 15:29:21"
        assert reader[1][1] == "12"
