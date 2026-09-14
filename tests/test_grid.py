# tests/test_grid.py
# ==============================================================================
# LITERATE TESTING STANDARD: GRID SUBSYSTEM VERIFICATION
# ==============================================================================
# This test module validates the spatial grid calculations, color conversions,
# high-visibility grid drawing, and image processing error handlers.

import cv2
import numpy as np

from src.core.grid import (
    draw_high_visibility_grid,
    get_cell_info_by_coords,
    hex_to_bgr,
    process_and_save_grid_image,
)


def test_hex_to_bgr():
    """
    Narrative: Hexadecimal color representations (e.g., '#00FFFF' or 'FF0000')
    must be correctly translated into OpenCV-compatible BGR (Blue, Green, Red) tuples
    where red and blue channels are swapped from RGB order.
    """
    # For Cyan '#00FFFF', Red=0, Green=255, Blue=255 -> BGR is (255, 255, 0).
    cyan_hex = "#00FFFF"
    expected_cyan_bgr = (255, 255, 0)
    assert hex_to_bgr(cyan_hex) == expected_cyan_bgr

    # For pure Red 'FF0000', Red=255, Green=0, Blue=0 -> BGR is (0, 0, 255).
    red_hex = "FF0000"
    expected_red_bgr = (0, 0, 255)
    assert hex_to_bgr(red_hex) == expected_red_bgr


def test_draw_high_visibility_grid():
    """
    Narrative: Drawing a high-visibility grid over an image must preserve the
    source image dimensions while generating expected metadata partitions and
    cell indexing for spatial quantification.
    """
    # We initialize a blank black canvas of dimensions 200x200 pixels.
    img_h, img_w = 200, 200
    img = np.zeros((img_h, img_w, 3), dtype=np.uint8)

    # We define grid parameters specifying 100x100 pixel cells.
    config = {
        "cell_width_px": 100,
        "cell_height_px": 100,
        "grid_thickness": 2,
        "grid_color": "#00FFFF",
        "text_color": "#000000",
        "text_size": 12,
    }

    # We process the grid overlay and retrieve the blended image and cell metadata.
    blended, meta = draw_high_visibility_grid(img, config)

    # The resulting blended image must maintain exact shape dimensions.
    assert blended.shape == (img_h, img_w, 3)

    # For a 200x200 image partitioned by 100x100 cells, exactly 4 cells are created.
    expected_cell_count = 4
    assert len(meta) == expected_cell_count

    # The primary cell index must start at 0.
    assert meta[0]["cell_number"] == 0


def test_get_cell_info_by_coords():
    """
    Narrative: Spatial coordinate mapping must correctly compute cell indices
    and interval ranges [start, end) while correctly clamping out-of-bounds or
    negative coordinates to valid domain boundaries.
    """
    config = {
        "cell_width_px": 100,
        "cell_height_px": 100,
    }

    # For coordinates (50, 50) on a 200x200 grid, the point falls within the first cell (0).
    # The mathematical intervals are computed as [0, 100) for both x and y axes.
    cell_idx, x_str, y_str = get_cell_info_by_coords(50, 50, 200, 200, config)
    assert cell_idx == 0
    assert x_str == "[0,100)"
    assert y_str == "[0,100)"

    # Negative coordinates must be clamped to the lower bound (0).
    cell_idx_neg, _, _ = get_cell_info_by_coords(-10, -10, 200, 200, config)
    assert cell_idx_neg == 0


def test_process_and_save_grid_image_success(tmp_path):
    """
    Narrative: End-to-end grid image processing must successfully load a raw image from disk,
    apply the grid overlay, save the processed result to the designated path,
    and return valid metadata.
    """
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
    """
    Narrative: When attempting to process a non-existent image path, cv2.imread returns None,
    triggering graceful failure handling that returns success=False and an empty metadata list.
    """
    config = {
        "cell_width_px": 100,
        "cell_height_px": 100,
        "grid_thickness": 2,
        "grid_color": "#00FFFF",
        "text_color": "#000000",
        "text_size": 12,
    }
    
    success, meta = process_and_save_grid_image("nonexistent_path_xyz.jpg", str(tmp_path / "out.jpg"), config)
    assert success is False
    assert meta == []


def test_process_and_save_grid_image_write_failure(tmp_path, monkeypatch):
    """
    Narrative: When file writing fails (mocked by forcing cv2.imwrite to return False),
    the processing pipeline must handle the error gracefully and return success=False.
    """
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

    # We mock cv2.imwrite to simulate a write failure.
    monkeypatch.setattr(cv2, "imwrite", lambda *args, **kwargs: False)

    success, meta = process_and_save_grid_image(str(raw_img), str(tmp_path / "fail_out.jpg"), config)
    assert success is False
    assert meta == []
