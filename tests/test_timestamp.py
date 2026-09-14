# tests/test_timestamp.py
# ==============================================================================
# LITERATE TESTING STANDARD: TIMESTAMP PARSING SUBSYSTEM VERIFICATION
# ==============================================================================
# This test module validates that timestamp parsing routines correctly extract,
# reformat, or gracefully fall back when processing various filename patterns.

from src.core.timestamp import parse_timestamp_from_filename


def test_parse_timestamp_valid():
    """
    Narrative: Given a standard filename containing valid date and time tokens
    matching the expected pattern ('IMG_YYYYMMDD_HHMMSS.jpg'), the parser must
    extract and format the timestamp into a standard human-readable string.
    """
    filename = "IMG_20260913_153045.jpg"
    
    # We parse the filename to extract and format the underlying timestamp.
    result = parse_timestamp_from_filename(filename)
    
    # The expected formatted output string is:
    #     "2026-09-13 15:30:45"
    assert result == "2026-09-13 15:30:45"


def test_parse_timestamp_non_conforming():
    """
    Narrative: When a filename does not conform to the expected structural token length
    or pattern, the parser must return the original filename string as a fallback.
    """
    filename = "photo_20260913.jpg"
    
    # Non-conforming filenames bypass parsing and return the original name.
    result = parse_timestamp_from_filename(filename)
    
    assert result == "photo_20260913"


def test_parse_timestamp_exception():
    """
    Narrative: When a filename matches token length but contains invalid date components
    that trigger an exception during datetime conversion, the routine must catch the error
    and safely return the original filename.
    """
    # An invalid date component forces an exception in datetime.strptime.
    filename = "IMG_INVALIDDATE_123456.jpg"
    
    result = parse_timestamp_from_filename(filename)
    
    # The fallback mechanism ensures the raw filename is returned intact.
    assert result == "IMG_INVALIDDATE_123456"
