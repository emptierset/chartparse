import pytest

from chartparse.instrument import StarPowerEvent


def StarPowerEventWithDefaults(
    tick=pytest.default_tick, timestamp=pytest.default_timestamp, sustain=pytest.default_sustain
):
    return StarPowerEvent(tick, timestamp, sustain)
