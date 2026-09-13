from src.core.timestamp import parse_timestamp_from_filename


def test_parse_timestamp_valid():
    filename = "IMG_20260913_153045.jpg"
    result = parse_timestamp_from_filename(filename)
    assert result == "2026-09-13 15:30:45"


def test_parse_timestamp_non_conforming():
    filename = "photo_20260913.jpg"
    result = parse_timestamp_from_filename(filename)
    assert result == "photo_20260913"


def test_parse_timestamp_exception():
    # Triggers exception in datetime.strptime and covers lines 22-28
    filename = "IMG_INVALIDDATE_123456.jpg"
    result = parse_timestamp_from_filename(filename)
    assert result == "IMG_INVALIDDATE_123456"
