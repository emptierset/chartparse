import pytest

import tests.helpers.lines


class TestGenerateValidBPMLine(object):
    def test_basic(self):
        assert tests.helpers.lines.generate_bpm(100, 120.000) == "  100 = B 120000"

    def test_raises(self):
        with pytest.raises(ValueError):
            _ = tests.helpers.lines.generate_bpm(100, 120.5555)


class TestGenerateValidTimeSignatureLine(object):
    def test_shortform(self):
        assert tests.helpers.lines.generate_time_signature(100, 4) == "  100 = TS 4"

    def test_longform(self):
        assert tests.helpers.lines.generate_time_signature(100, 4, 8) == "  100 = TS 4 3"


class TestGenerateValidStarPowerLine(object):
    def test_basic(self):
        assert tests.helpers.lines.generate_star_power(100, 1000) == "  100 = S 2 1000"


class TestGenerateValidNoteLine(object):
    def test_basic(self):
        assert tests.helpers.lines.generate_note(100, 0, 1000) == "  100 = N 0 1000"
