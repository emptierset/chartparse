import pytest

from chartparse.globalevents import GlobalEvent


def GlobalEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    value=pytest.defaults.global_event_value,
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
):
    return GlobalEvent(tick, timestamp, value, proximal_bpm_event_index=proximal_bpm_event_index)
