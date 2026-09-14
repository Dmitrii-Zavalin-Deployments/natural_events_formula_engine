# tests/test_measure_object.py
# ==============================================================================
# LITERATE TESTING STANDARD: MAIN APPLICATION EXECUTABLE VERIFICATION
# ==============================================================================
# This test module validates the core entrypoint behaviors, error-handling routines,
# configuration validations, and execution flows for dry-run and measurement modes.

import cv2
import numpy as np
import pytest

from measure_object import main


def test_main_config_load_error(monkeypatch):
    """
    Narrative: When configuration loading fails with an exception, the application
    must catch the error and terminate execution with a system exit code of 1.
    """
    # We patch configuration loading to raise a ValueError simulating corrupt config files.
    monkeypatch.setattr("measure_object.load_config", lambda: (_ for _ in ()).throw(ValueError("Invalid config")))
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1


def test_main_missing_config_key(monkeypatch, tmp_path):
    """
    Narrative: When required configuration keys (such as the 'grid' specification)
    are missing, the application must detect the schema violation and exit cleanly with code 1.
    """
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    # We construct a configuration dictionary lacking the required 'grid' dictionary.
    config_data = {
        "mode": "dry_run",
        "paths": {
            "raw_folder": str(raw_dir),
            "processed_folder": str(tmp_path / "processed"),
            "output_csv": str(tmp_path / "out.csv")
        }
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1


def test_main_invalid_execution_mode(monkeypatch, tmp_path):
    """
    Narrative: Providing an unrecognized execution mode string must trigger validation
    failures resulting in program termination with exit code 1.
    """
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    config_data = {
        "mode": "unknown_mode",
        "paths": {
            "raw_folder": str(raw_dir),
            "processed_folder": str(tmp_path / "processed"),
            "output_csv": str(tmp_path / "out.csv")
        },
        "grid": {"cell_width_px": 100, "cell_height_px": 100, "grid_thickness": 1, "grid_color": "#000000", "text_color": "#ffffff"}
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1


def test_main_raw_folder_not_exists(monkeypatch, tmp_path):
    """
    Narrative: Specifying a raw input directory path that does not exist on disk
    must cause the application to abort execution with exit code 1.
    """
    config_data = {
        "mode": "dry_run",
        "paths": {
            "raw_folder": str(tmp_path / "nonexistent_raw"),
            "processed_folder": str(tmp_path / "processed"),
            "output_csv": str(tmp_path / "out.csv")
        },
        "grid": {"cell_width_px": 100, "cell_height_px": 100, "grid_thickness": 1, "grid_color": "#000000", "text_color": "#ffffff"}
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1


def test_main_no_valid_images(monkeypatch, tmp_path):
    """
    Narrative: When the raw input directory contains no valid image files matching
    supported extensions, the application must terminate gracefully with exit code 1.
    """
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    config_data = {
        "mode": "dry_run",
        "paths": {
            "raw_folder": str(raw_dir),
            "processed_folder": str(tmp_path / "processed"),
            "output_csv": str(tmp_path / "out.csv")
        },
        "grid": {"cell_width_px": 100, "cell_height_px": 100, "grid_thickness": 1, "grid_color": "#000000", "text_color": "#ffffff"}
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1


def test_main_grid_image_read_failure(monkeypatch, tmp_path):
    """
    Narrative: If grid processing fails on an image (returning success=False),
    the main loop must handle the failure gracefully without crashing the batch run.
    """
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    img_path = raw_dir / "IMG_20260913_120000.jpg"
    dummy = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(str(img_path), dummy)

    config_data = {
        "mode": "dry_run",
        "paths": {
            "raw_folder": str(raw_dir),
            "processed_folder": str(tmp_path / "processed"),
            "output_csv": str(tmp_path / "out.csv")
        },
        "grid": {"cell_width_px": 100, "cell_height_px": 100, "grid_thickness": 1, "grid_color": "#000000", "text_color": "#ffffff"}
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    
    # We force process_and_save_grid_image to return (False, []) to test error handling logic.
    monkeypatch.setattr("measure_object.process_and_save_grid_image", lambda *args, **kwargs: (False, []))
    
    main()


def test_main_dry_run_success(monkeypatch, tmp_path):
    """
    Narrative: Executing the application in 'dry_run' mode with valid input images
    must successfully process and complete the batch workflow without raising exceptions.
    """
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    img_path = raw_dir / "IMG_20260913_120000.jpg"
    dummy = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.imwrite(str(img_path), dummy)

    config_data = {
        "mode": "dry_run",
        "paths": {
            "raw_folder": str(raw_dir),
            "processed_folder": str(tmp_path / "processed"),
            "output_csv": str(tmp_path / "out.csv")
        },
        "grid": {"cell_width_px": 100, "cell_height_px": 100, "grid_thickness": 1, "grid_color": "#000000", "text_color": "#ffffff"}
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    
    main()


def test_main_measurements_success_and_none_result(monkeypatch, tmp_path):
    """
    Narrative: In 'measurements' mode, if coordinate extraction initially returns None,
    the application must handle null results gracefully and successfully persist subsequent valid measurements to CSV.
    """
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    img_path = raw_dir / "IMG_20260913_120000.jpg"
    dummy = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.imwrite(str(img_path), dummy)

    config_data = {
        "mode": "measurements",
        "paths": {
            "raw_folder": str(raw_dir),
            "processed_folder": str(tmp_path / "processed"),
            "output_csv": str(tmp_path / "out.csv")
        },
        "grid": {"cell_width_px": 100, "cell_height_px": 100, "grid_thickness": 1, "grid_color": "#000000", "text_color": "#ffffff"}
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    monkeypatch.setattr("builtins.input", lambda prompt="": "0")
    monkeypatch.setattr("webbrowser.open", lambda url: True)
    
    # We mock process_image to return None on the first invocation, then valid coordinates on retry.
    call_count = 0
    def mock_process_image(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return None
        return (50.0, 50.0)

    monkeypatch.setattr("measure_object.process_image", mock_process_image)

    main()
    
    # We verify that the output CSV file was successfully generated and populated.
    assert (tmp_path / "out.csv").exists()
