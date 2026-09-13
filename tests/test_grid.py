import cv2
import numpy as np

from src.core.grid import (
    draw_high_visibility_grid,
    get_cell_info_by_coords,
    hex_to_bgr,
    process_and_save_grid_image,
)


def test_hex_to_bgr():
    assert hex_to_bgr("#00FFFF") == (255, 255, 0)
    assert hex_to_bgr("FF0000") == (0, 0, 255)


def test_draw_high_visibility_grid():
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    config = {
        "cell_width_px": 100,
        "cell_height_px": 100,
        "grid_thickness": 2,
        "grid_color": "#00FFFF",
        "text_color": "#000000",
        "text_size": 12,
    }
    blended, meta = draw_high_visibility_grid(img, config)
    assert blended.shape == (200, 200, 3)
    assert len(meta) == 4
    assert meta[0]["cell_number"] == 0


def test_get_cell_info_by_coords():
    config = {
        "cell_width_px": 100,
        "cell_height_px": 100,
    }
    # Normal coords
    cell_idx, x_str, y_str = get_cell_info_by_coords(50, 50, 200, 200, config)
    assert cell_idx == 0
    assert x_str == "[0,100)"
    assert y_str == "[0,100)"

    # Negative coords clamping
    cell_idx_neg, _, _ = get_cell_info_by_coords(-10, -10, 200, 200, config)
    assert cell_idx_neg == 0


def test_process_and_save_grid_image_success(tmp_path):
    raw_img = tmp_path / "raw.jpg"
    processed_img = tmp_path / "processed.jpg"
    
    dummy = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.imwrite(str(raw_img), dummy)

    config = {
        "cell_width_px": 100,
        "cell_height_px": 100,
        "grid_thickness": 2,
        "grid_color": "#00FFFF",
        "text_color": "#000000",
        "text_size": 12,
    }

    success, meta = process_and_save_grid_image(str(raw_img), str(processed_img), config)
    assert success is True
    assert len(meta) == 4
    assert processed_img.exists()


def test_process_and_save_grid_image_read_failure(tmp_path):
    config = {
        "cell_width_px": 100,
        "cell_height_px": 100,
        "grid_thickness": 2,
        "grid_color": "#00FFFF",
        "text_color": "#000000",
        "text_size": 12,
    }
    # Non-existent path causes cv2.imread to return None (Lines 107-110)
    success, meta = process_and_save_grid_image("nonexistent_path_xyz.jpg", str(tmp_path / "out.jpg"), config)
    assert success is False
    assert meta == []


def test_process_and_save_grid_image_write_failure(tmp_path, monkeypatch):
    raw_img = tmp_path / "raw.jpg"
    dummy = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.imwrite(str(raw_img), dummy)

    config = {
        "cell_width_px": 100,
        "cell_height_px": 100,
        "grid_thickness": 2,
        "grid_color": "#00FFFF",
        "text_color": "#000000",
        "text_size": 12,
    }

    # Force cv2.imwrite to return False to test lines 116-117
    monkeypatch.setattr(cv2, "imwrite", lambda *args, **kwargs: False)

    success, meta = process_and_save_grid_image(str(raw_img), str(tmp_path / "fail_out.jpg"), config)
    assert success is False
    assert meta == []
