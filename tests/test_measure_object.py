import cv2
import numpy as np
import pytest

from measure_object import main


def test_main_config_load_error(monkeypatch):
    monkeypatch.setattr("measure_object.load_config", lambda: (_ for _ in ()).throw(ValueError("Invalid config")))
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_missing_config_key(monkeypatch, tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    # Missing 'grid' key
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
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    config_data = {
        "mode": "unknown_mode",
        "paths": {
            "raw_folder": str(raw_dir),
            "processed_folder": str(tmp_path / "processed"),
            "output_csv": str(tmp_path / "out.csv")
        },
        "grid": {"cell_width_px": 100, "cell_height_px": 100, "grid_thickness": 1, "grid_color": "#000", "text_color": "#fff"}
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_raw_folder_not_exists(monkeypatch, tmp_path):
    config_data = {
        "mode": "dry_run",
        "paths": {
            "raw_folder": str(tmp_path / "nonexistent_raw"),
            "processed_folder": str(tmp_path / "processed"),
            "output_csv": str(tmp_path / "out.csv")
        },
        "grid": {"cell_width_px": 100, "cell_height_px": 100, "grid_thickness": 1, "grid_color": "#000", "text_color": "#fff"}
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_no_valid_images(monkeypatch, tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    config_data = {
        "mode": "dry_run",
        "paths": {
            "raw_folder": str(raw_dir),
            "processed_folder": str(tmp_path / "processed"),
            "output_csv": str(tmp_path / "out.csv")
        },
        "grid": {"cell_width_px": 100, "cell_height_px": 100, "grid_thickness": 1, "grid_color": "#000", "text_color": "#fff"}
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_grid_image_read_failure(monkeypatch, tmp_path):
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
        "grid": {"cell_width_px": 100, "cell_height_px": 100, "grid_thickness": 1, "grid_color": "#000", "text_color": "#fff"}
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    # Force process_and_save_grid_image to return (False, []) to trigger lines 78-79
    monkeypatch.setattr("measure_object.process_and_save_grid_image", lambda *args, **kwargs: (False, []))

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_dry_run_success(monkeypatch, tmp_path):
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
        "grid": {"cell_width_px": 100, "cell_height_px": 100, "grid_thickness": 1, "grid_color": "#000", "text_color": "#fff"}
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    main()


def test_main_measurements_success_and_none_result(monkeypatch, tmp_path):
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
        "grid": {"cell_width_px": 100, "cell_height_px": 100, "grid_thickness": 1, "grid_color": "#000", "text_color": "#fff"}
    }
    monkeypatch.setattr("measure_object.load_config", lambda: config_data)
    monkeypatch.setattr("builtins.input", lambda prompt="": "0")
    monkeypatch.setattr("webbrowser.open", lambda url: True)
    
    # Mock process_image to return None first (triggering lines 124-125), then valid coordinates
    call_count = 0
    def mock_process_image(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return None
        return (50.0, 50.0)

    monkeypatch.setattr("measure_object.process_image", mock_process_image)

    main()
    assert (tmp_path / "out.csv").exists()
