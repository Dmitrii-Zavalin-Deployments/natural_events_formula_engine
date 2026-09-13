import cv2
import numpy as np
import pytest

from src.core import template_matching


@pytest.fixture(autouse=True)
def reset_globals():
    template_matching.OBJECT_TEMPLATE = None
    template_matching.OBJECT_OFFSET_X = 0
    template_matching.OBJECT_OFFSET_Y = 0
    yield
    template_matching.OBJECT_TEMPLATE = None


def test_process_image_read_failure(tmp_path):
    out_path = tmp_path / "marked.jpg"
    res = template_matching.process_image("nonexistent_file_12345.jpg", str(out_path))
    assert res is None


def test_init_object_template_empty_roi():
    # Tiny image causes zero-size ROI (Covering lines 25-27)
    tiny_img = np.zeros((1, 1, 3), dtype=np.uint8)
    template_matching.init_object_template(tiny_img)
    assert template_matching.OBJECT_TEMPLATE is not None
    assert template_matching.OBJECT_TEMPLATE.size > 0


def test_init_object_template_no_hough_lines():
    # Solid image has no edges/lines (Covering lines 34-40)
    solid_img = np.ones((200, 200, 3), dtype=np.uint8) * 128
    template_matching.init_object_template(solid_img)
    assert template_matching.OBJECT_TEMPLATE is not None


def test_init_object_template_no_horizontal_line(monkeypatch):
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    # Mock HoughLinesP to return only vertical lines so no horizontal line meets criteria (Covering lines 55-57)
    monkeypatch.setattr(cv2, "HoughLinesP", lambda *args, **kwargs: np.array([[[10, 10, 10, 60]]]))
    template_matching.init_object_template(img)
    assert template_matching.OBJECT_TEMPLATE is not None


def test_find_object_xy_small_search_area():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    # Set a large template so search area is smaller than template dimensions (Covering lines 85-86)
    template_matching.OBJECT_TEMPLATE = np.zeros((80, 80, 3), dtype=np.uint8)
    x, y, box = template_matching.find_object_xy(img)
    assert x is not None
    assert y is not None
    assert len(box) == 4


def test_process_image_success(tmp_path):
    raw_path = tmp_path / "raw.jpg"
    processed_path = tmp_path / "processed.jpg"

    # Create an image with a clear horizontal line in the ROI zone
    img = np.ones((300, 300, 3), dtype=np.uint8) * 255
    cv2.line(img, (50, 200), (90, 200), (0, 0, 0), 2)
    cv2.imwrite(str(raw_path), img)

    x, y = template_matching.process_image(str(raw_path), str(processed_path))
    assert isinstance(x, float)
    assert isinstance(y, float)
    assert processed_path.exists()
