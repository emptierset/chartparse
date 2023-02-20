from __future__ import annotations

import pytest

import chartparse.tick
from chartparse.tick import NoteDuration, Tick, Ticks
from tests.helpers import testcase


class TestAdd(object):
    def test(self) -> None:
        want = Tick(3)
        got = chartparse.tick.add(Tick(1), Ticks(2))
        assert got == want


class TestSum(object):
    def test(self) -> None:
        want = Ticks(3)
        got = chartparse.tick.sum(Ticks(1), Ticks(2))
        assert got == want


class TestDifference(object):
    def test(self) -> None:
        want = Ticks(1)
        got = chartparse.tick.difference(Ticks(3), Ticks(2))
        assert got == want


class TestBetween(object):
    def test(self) -> None:
        want = Ticks(2)
        got = chartparse.tick.between(Tick(1), Tick(3))
        assert got == want


class TestNoteDurationToTicks(object):
    @testcase.parametrize(
        ["resolution", "note_duration", "want"],
        [
            testcase.new_anonymous(
                resolution=100,
                note_duration=NoteDuration.QUARTER,
                want=100,
            ),
            testcase.new_anonymous(
                resolution=192,
                note_duration=NoteDuration.QUARTER,
                want=192,
            ),
            testcase.new_anonymous(
                resolution=192,
                note_duration=NoteDuration.EIGHTH,
                want=96,
            ),
            testcase.new_anonymous(
                resolution=192,
                note_duration=NoteDuration.EIGHTH_TRIPLET,
                want=64,
            ),
            testcase.new_anonymous(
                resolution=192,
                note_duration=NoteDuration.SIXTEENTH_TRIPLET,
                want=32,
            ),
        ],
    )
    def test(self, resolution: Ticks, note_duration: NoteDuration, want: Ticks) -> None:
        got = chartparse.tick.note_duration_to_ticks(resolution, note_duration)
        assert got == want


class TestSecondsFromTicksAtBPM(object):
    @testcase.parametrize(
        ["ticks", "bpm", "resolution", "want"],
        [
            testcase.new_anonymous(
                ticks=100,
                bpm=60,
                resolution=100,
                want=1,
            ),
            testcase.new_anonymous(
                ticks=100,
                bpm=120,
                resolution=100,
                want=0.5,
            ),
            testcase.new_anonymous(
                ticks=200,
                bpm=120,
                resolution=100,
                want=1,
            ),
            testcase.new_anonymous(
                ticks=400,
                bpm=200,
                resolution=100,
                want=1.2,
            ),
            testcase.new_anonymous(
                ticks=100,
                bpm=60,
                resolution=200,
                want=0.5,
            ),
        ],
    )
    def test(self, ticks: Ticks, bpm: float, resolution: Ticks, want: float) -> None:
        got = chartparse.tick.seconds_from_ticks_at_bpm(ticks, bpm, resolution)
        assert got == want

    @testcase.parametrize(
        ["ticks", "bpm", "resolution"],
        [
            testcase.new(
                "negative_ticks",
                ticks=-1,
                bpm=120.000,
                resolution=192,
            ),
            testcase.new(
                "negative_bpm",
                ticks=0,
                bpm=-1,
                resolution=192,
            ),
            testcase.new(
                "zero_bpm",
                ticks=0,
                bpm=0,
                resolution=192,
            ),
            testcase.new(
                "negative_resolution",
                ticks=0,
                bpm=120.000,
                resolution=-1,
            ),
            testcase.new(
                "zero_resolution",
                ticks=0,
                bpm=120.000,
                resolution=0,
            ),
        ],
    )
    def test_error(self, ticks: Ticks, bpm: float, resolution: Ticks) -> None:
        with pytest.raises(ValueError):
            _ = chartparse.tick.seconds_from_ticks_at_bpm(ticks, bpm, resolution)
