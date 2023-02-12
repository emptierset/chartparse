from __future__ import annotations

import pytest

import tests.helpers.lines
from chartparse.instrument import NoteTrackIndex
from chartparse.tick import Tick, Ticks
from tests.helpers import defaults


class TestGenerateValidBPMLine(object):
    def test(self) -> None:
        want = "  100 = B 120000"
        got = tests.helpers.lines.generate_bpm(Tick(100), 120.000)
        assert got == want

    def test_raises(self) -> None:
        with pytest.raises(ValueError):
            _ = tests.helpers.lines.generate_bpm(
                defaults.tick,
                defaults.bpm + 0.0001,
            )


class TestGenerateValidTimeSignatureLine(object):
    def test_shortform(self) -> None:
        want = "  100 = TS 4"
        got = tests.helpers.lines.generate_time_signature(Tick(100), 4)
        assert got == want

    def test_longform(self) -> None:
        want = "  100 = TS 4 3"
        got = tests.helpers.lines.generate_time_signature(Tick(100), 4, 3)
        assert got == want


class TestGenerateValidStarPowerLine(object):
    def test(self) -> None:
        want = "  100 = S 2 1000"
        got = tests.helpers.lines.generate_star_power(Tick(100), Ticks(1000))
        assert got == want


class TestGenerateValidNoteLine(object):
    def test(self) -> None:
        want = f"  100 = N {NoteTrackIndex.G.value} 1000"
        got = tests.helpers.lines.generate_note(Tick(100), NoteTrackIndex.G, Ticks(1000))
        assert got == want
