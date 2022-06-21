import re

from chartparse.event import Event, FromChartLineMixin
from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.track import EventTrack
from chartparse.util import DictPropertiesEqMixin


class SyncTrack(EventTrack, DictPropertiesEqMixin):
    def __init__(self, time_signature_events, bpm_events):
        if not time_signature_events:
            raise ValueError("time_signature_events must not be empty")
        if time_signature_events[0].tick != 0:
            raise ValueError(
                f"first TimeSignatureEvent {time_signature_events[0]} must have tick 0"
            )
        if not bpm_events:
            raise ValueError("bpm_events must not be empty")
        if bpm_events[0].tick != 0:
            raise ValueError(f"first BPMEvent {bpm_events[0]} must have tick 0")

        self.time_signature_events = time_signature_events
        self.bpm_events = bpm_events

    @classmethod
    def from_chart_lines(cls, iterator_getter):
        time_signature_events = cls._parse_events_from_iterable(
            iterator_getter(), TimeSignatureEvent.from_chart_line
        )
        bpm_events = cls._parse_events_from_iterable(iterator_getter(), BPMEvent.from_chart_line)
        return cls(time_signature_events, bpm_events)

    def idx_of_proximal_bpm_event(self, tick, start_idx=0):
        # A BPMEvent is "proximal" relative to tick `T` if it is the
        # BPMEvent with the highest tick value not greater than `T`.
        for idx in range(start_idx, len(self.bpm_events)):
            is_last_bpm_event = idx == len(self.bpm_events) - 1
            next_bpm_event = self.bpm_events[idx + 1] if not is_last_bpm_event else None
            if is_last_bpm_event or next_bpm_event.tick > tick:
                return idx
        raise ValueError(f"there are no BPMEvents at or after index {start_idx} in bpm_events")


class TimeSignatureEvent(Event):
    # Match 1: Tick
    # Match 2: Upper numeral
    # Match 3: Lower numeral (optional; assumed to be 4 if absent)
    _regex = r"^\s*?(\d+?) = TS (\d+?)(?: (\d+?))?\s*?$"
    _regex_prog = re.compile(_regex)

    def __init__(self, tick, upper_numeral, lower_numeral, timestamp=None):
        super().__init__(tick, timestamp=timestamp)
        self.upper_numeral = upper_numeral
        self.lower_numeral = lower_numeral

    @classmethod
    def from_chart_line(cls, line):
        m = cls._regex_prog.match(line)
        if not m:
            raise RegexFatalNotMatchError(cls._regex, line)
        tick, upper_numeral = int(m.group(1)), int(m.group(2))
        # The lower number is written by Moonscraper as the log2 of the true value.
        lower_numeral = 2 ** int(m.group(3)) if m.group(3) else 4
        return cls(tick, upper_numeral, lower_numeral)

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.upper_numeral}/{self.lower_numeral}")
        return "".join(to_join)


class BPMEvent(Event, FromChartLineMixin):
    # Match 1: Tick
    # Match 2: BPM (the last 3 digits are the decimal places)
    _regex = r"^\s*?(\d+?) = B (\d+?)\s*?$"
    _regex_prog = re.compile(_regex)

    def __init__(self, tick, bpm, timestamp=None):
        super().__init__(tick, timestamp=timestamp)
        self.bpm = bpm

    @classmethod
    def from_chart_line(cls, line):
        event = super().from_chart_line(line)
        raw_bpm = event.bpm
        bpm_whole_part_str, bpm_decimal_part_str = raw_bpm[:-3], raw_bpm[-3:]
        bpm_whole_part = int(bpm_whole_part_str) if bpm_whole_part_str != "" else 0
        bpm_decimal_part = int(bpm_decimal_part_str) / 1000
        bpm = bpm_whole_part + bpm_decimal_part
        event.bpm = bpm
        return event

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.bpm} BPM")
        return "".join(to_join)
