import pytest

from tests.conftest import (
    generate_valid_bpm_line_fn,
    generate_valid_note_line_fn,
    generate_valid_star_power_line_fn,
    generate_valid_time_signature_line_fn,
)


class TestGenerateValidBPMLine(object):
    def test_basic(self):
        assert generate_valid_bpm_line_fn(100, 120.000) == "  100 = B 120000"

    def test_raises(self):
        with pytest.raises(ValueError):
            _ = generate_valid_bpm_line_fn(100, 120.5555)


class TestGenerateValidTimeSignatureLine(object):
    def test_shortform(self):
        assert generate_valid_time_signature_line_fn(100, 4) == "  100 = TS 4"

    def test_longform(self):
        assert generate_valid_time_signature_line_fn(100, 4, 8) == "  100 = TS 4 3"


class TestGenerateValidStarPowerLine(object):
    def test_basic(self):
        assert generate_valid_star_power_line_fn(100, 1000) == "  100 = S 2 1000"


class TestGenerateValidNoteLine(object):
    def test_basic(self):
        assert generate_valid_note_line_fn(100, 0, 1000) == "  100 = N 0 1000"
