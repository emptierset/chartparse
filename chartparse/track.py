from chartparse.event import BPMEvent, TimeSignatureEvent
from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.util import DictPropertiesEqMixin


class SyncTrack(DictPropertiesEqMixin):
    def __init__(self, iterator_getter):
        self.time_signature_events = _parse_events_from_iterable(
            iterator_getter(), TimeSignatureEvent.from_chart_line
        )
        if self.time_signature_events[0].tick != 0:
            raise ValueError(
                f"first TimeSignatureEvent {self.time_signature_events[0]} must have tick 0"
            )

        self.bpm_events = _parse_events_from_iterable(iterator_getter(), BPMEvent.from_chart_line)
        if self.bpm_events[0].tick != 0:
            raise ValueError(f"first BPMEvent {self.bpm_events[0]} must have tick 0")

    def idx_of_proximal_bpm_event(self, tick, start_idx=0):
        # A BPMEvent is "proximal" relative to tick `T` if it is the
        # BPMEvent with the highest tick value not greater than `T`.
        for idx in range(start_idx, len(self.bpm_events)):
            is_last_bpm_event = idx == len(self.bpm_events) - 1
            next_bpm_event = self.bpm_events[idx + 1] if not is_last_bpm_event else None
            if is_last_bpm_event or next_bpm_event.tick > tick:
                return idx
        raise ValueError(f"there are no BPMEvents at or after index {start_idx} in bpm_events")


def _parse_events_from_iterable(iterable, from_chart_line_fn):
    events = []
    for line in iterable:
        try:
            event = from_chart_line_fn(line)
        except RegexFatalNotMatchError:
            continue
        events.append(event)
    events.sort(key=lambda e: e.tick)
    return events
