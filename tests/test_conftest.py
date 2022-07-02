import pytest

from tests.conftest import (
    generate_valid_bpm_line_fn,
    generate_valid_note_line_fn,
    generate_valid_star_power_line_fn,
    generate_valid_time_signature_line_fn,
)


def test_generate_valid_bpm_line():
    assert generate_valid_bpm_line_fn(100, 120.000) == "  100 = B 120000"


def test_generate_valid_bpm_line_raises_ValueError():
    with pytest.raises(ValueError):
        _ = generate_valid_bpm_line_fn(100, 120.5555)


def test_generate_valid_time_signature_line_short():
    assert generate_valid_time_signature_line_fn(100, 4) == "  100 = TS 4"


def test_generate_valid_time_signature_line_long():
    assert generate_valid_time_signature_line_fn(100, 4, 8) == "  100 = TS 4 3"


def test_generate_valid_star_power_line():
    assert generate_valid_star_power_line_fn(100, 1000) == "  100 = S 2 1000"


def test_generate_valid_note_line():
    assert generate_valid_note_line_fn(100, 0, 1000) == "  100 = N 0 1000"
