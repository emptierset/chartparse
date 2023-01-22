from __future__ import annotations

import pytest

import tests.helpers.lines
from tests.helpers import defaults


class TestGenerateValidBPMLine(object):
    def test(self):
        got = tests.helpers.lines.generate_bpm(100, 120.000)
        assert got == "  100 = B 120000"

    def test_raises(self):
        with pytest.raises(ValueError):
            _ = tests.helpers.lines.generate_bpm(
                defaults.tick,
                defaults.bpm + 0.0001,
            )


class TestGenerateValidTimeSignatureLine(object):
    def test_shortform(self):
        got = tests.helpers.lines.generate_time_signature(100, 4)
        assert got == "  100 = TS 4"

    def test_longform(self):
        got = tests.helpers.lines.generate_time_signature(100, 4, 3)
        assert got == "  100 = TS 4 3"


class TestGenerateValidStarPowerLine(object):
    def test(self):
        got = tests.helpers.lines.generate_star_power(100, 1000)
        assert got == "  100 = S 2 1000"


class TestGenerateValidNoteLine(object):
    def test(self):
        got = tests.helpers.lines.generate_note(100, 0, 1000)
        assert got == "  100 = N 0 1000"
