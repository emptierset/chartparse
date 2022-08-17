import pytest

from chartparse.instrument import StarPowerEvent, NoteEvent


def StarPowerEventWithDefaults(
    *, tick=pytest.default_tick, timestamp=pytest.default_timestamp, sustain=pytest.default_sustain
):
    return StarPowerEvent(tick, timestamp, sustain)


def NoteEventWithDefaults(
    *,
    tick=pytest.default_tick,
    timestamp=pytest.default_timestamp,
    note=pytest.default_note,
    sustain=pytest.default_sustain,
    is_forced=False,
    is_tap=False,
    star_power_data=None,
):
    return NoteEvent(tick, timestamp, note, sustain, is_forced, is_tap, star_power_data)
