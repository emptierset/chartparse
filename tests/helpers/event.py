from chartparse.event import Event
from chartparse.tick import Tick
from chartparse.time import Timestamp
from tests.helpers import defaults


def EventWithDefaults(
    *,
    tick: Tick = defaults.tick,
    timestamp: Timestamp = defaults.timestamp,
    _proximal_bpm_event_index: int = defaults.proximal_bpm_event_index,
) -> Event:
    return Event(
        tick=tick,
        timestamp=timestamp,
        _proximal_bpm_event_index=_proximal_bpm_event_index,
    )
