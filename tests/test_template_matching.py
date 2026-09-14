# tests/test_template_matching.py
# ==============================================================================
# LITERATE TESTING STANDARD: TEMPLATE MATCHING SUBSYSTEM VERIFICATION
# ==============================================================================
# This test module validates template initialization, ROI fallback strategies,
# coordinate search routines, and image processing error handlers for the template matching engine.

import cv2
import numpy as np
import pytest

from src.core import template_matching


@pytest.fixture(autouse=True)
def reset_globals():
    """
    Narrative: We ensure test isolation by resetting global module state variables
    before and after each test execution.
    """
    template_matching.OBJECT_TEMPLATE = None
    template_matching.OBJECT_OFFSET_X = 0
    template_matching.OBJECT_OFFSET_Y = 0
    yield
    template_matching.OBJECT_TEMPLATE = None


def test_process_image_read_failure(tmp_path):
    """
    Narrative: Attempting to process a non-existent image file must return None
    to signal a graceful read failure.
    """
    out_path = tmp_path / "marked.jpg"
    
    # We pass an invalid file path to trigger image read failure.
    res = template_matching.process_image("nonexistent_file_12345.jpg", str(out_path))
    assert res is None


def test_init_object_template_empty_roi():
    """
    Narrative: A tiny 1x1 input image triggers an empty Region of Interest (ROI),
    exercising fallback template initialization logic.
    """
    # We initialize a 1x1 pixel black image to trigger edge-case ROI extraction.
    tiny_img = np.zeros((1, 1, 3), dtype=np.uint8)
    template_matching.init_object_template(tiny_img)
    
    # The template must be successfully initialized despite the minimal dimensions.
    assert template_matching.OBJECT_TEMPLATE is not None
    assert template_matching.OBJECT_TEMPLATE.size > 0


def test_init_object_template_no_hough_lines():
    """
    Narrative: When an image contains no discernible lines (e.g., solid gray canvas),
    template initialization must fall back gracefully without failing.
    """
    solid_img = np.ones((200, 200, 3), dtype=np.uint8) * 128
    template_matching.init_object_template(solid_img)
    
    assert template_matching.OBJECT_TEMPLATE is not None


def test_init_object_template_no_horizontal_line(monkeypatch):
    """
    Narrative: When Hough lines detection yields no horizontal lines, the template
    initialization routine must execute fallback logic successfully.
    """
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    
    # We mock HoughLinesP to return non-horizontal line segments.
    monkeypatch.setattr(cv2, "HoughLinesP", lambda *args, **kwargs: np.array([[[10, 10, 10, 60]]]))
    template_matching.init_object_template(img)
    
    assert template_matching.OBJECT_TEMPLATE is not None


def test_find_object_xy_small_search_area():
    """
    Narrative: Searching for an object when template dimensions approach or match
    search image boundaries must still resolve valid coordinates and bounding boxes.
    """
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    template_matching.OBJECT_TEMPLATE = np.zeros((80, 80, 3), dtype=np.uint8)
    
    x, y, box = template_matching.find_object_xy(img)
    
    assert x is not None
    assert y is not None
    assert len(box) == 4


def test_process_image_success(tmp_path):
    """
    Narrative: End-to-end processing of a valid synthetic image containing a drawn line
    must successfully compute floating-point coordinates and write the processed output.
    """
    raw_path = tmp_path / "raw.jpg"
    processed_path = tmp_path / "processed.jpg"

    # We synthesize a white image with a black horizontal line feature.
    img = np.ones((300, 300, 3), dtype=np.uint8) * 255
    cv2.line(img, (50, 200), (90, 200), (0, 0, 0), 2)
    cv2.imwrite(str(raw_path), img)

    # We execute the image processing pipeline.
    x, y = template_matching.process_image(str(raw_path), str(processed_path))
    
    assert isinstance(x, float)
    assert isinstance(y, float)
    assert processed_path.exists()
