from chartparse.event import Event
from tests.helpers import defaults


def EventWithDefaults(
    *,
    tick=defaults.tick,
    timestamp=defaults.timestamp,
    _proximal_bpm_event_index=defaults.proximal_bpm_event_index,
):
    return Event(
        tick=tick,
        timestamp=timestamp,
        _proximal_bpm_event_index=_proximal_bpm_event_index,
    )
