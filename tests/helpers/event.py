from chartparse.event import Event
from tests.helpers import defaults


def EventWithDefaults(
    *,
    tick=defaults.tick,
    timestamp=defaults.timestamp,
    # TODO: add prepended _ to proximal_bpm... param for all default event factories. This is to
    # standardize with the actual object signatures.
    proximal_bpm_event_index=defaults.proximal_bpm_event_index,
):
    return Event(
        tick=tick,
        timestamp=timestamp,
        _proximal_bpm_event_index=proximal_bpm_event_index,
    )
