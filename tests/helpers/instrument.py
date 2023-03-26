from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta

from chartparse.exceptions import UnreachableError
from chartparse.instrument import (
    ComplexSustain,
    Difficulty,
    HOPOState,
    Instrument,
    InstrumentTrack,
    Note,
    NoteEvent,
    NoteTrackIndex,
    SpecialEvent,
    StarPowerData,
    StarPowerEvent,
    SustainTuple,
    TrackEvent,
)
from chartparse.tick import Tick, Ticks
from chartparse.time import Timestamp
from tests.helpers import defaults


def InstrumentTrackWithDefaults(
    *,
    instrument: Instrument = defaults.instrument,
    difficulty: Difficulty = defaults.difficulty,
    note_events: Sequence[NoteEvent] = [defaults.note_event],
    star_power_events: Sequence[StarPowerEvent] = [defaults.star_power_event],
    track_events: Sequence[TrackEvent] = [defaults.track_event],
) -> InstrumentTrack:
    return InstrumentTrack(
        instrument=instrument,
        difficulty=difficulty,
        note_events=note_events,
        star_power_events=star_power_events,
        track_events=track_events,
    )


def SpecialEventWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    timestamp: Timestamp | timedelta = defaults.timestamp,
    sustain: Ticks | int = defaults.sustain,
    _proximal_bpm_event_index: int = defaults.proximal_bpm_event_index,
    init_end_tick: bool = False,
) -> SpecialEvent:
    s = SpecialEvent(
        tick=Tick(tick),
        timestamp=Timestamp(timestamp),
        sustain=Ticks(sustain),
        _proximal_bpm_event_index=_proximal_bpm_event_index,
    )
    if init_end_tick:
        s.end_tick  # accessing this initializes it because it's a cached_property
    return s


def SpecialEventParsedDataWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    sustain: Ticks | int = defaults.sustain,
) -> SpecialEvent.ParsedData:
    return SpecialEvent.ParsedData(tick=Tick(tick), sustain=Ticks(sustain))


def StarPowerEventWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    timestamp: Timestamp | timedelta = defaults.timestamp,
    sustain: Ticks | int = defaults.sustain,
    _proximal_bpm_event_index: int = defaults.proximal_bpm_event_index,
    init_end_tick: bool = False,
) -> StarPowerEvent:
    s = StarPowerEvent(
        tick=Tick(tick),
        timestamp=Timestamp(timestamp),
        sustain=Ticks(sustain),
        _proximal_bpm_event_index=_proximal_bpm_event_index,
    )
    if init_end_tick:
        s.end_tick  # accessing this initializes it because it's a cached_property
    return s


def NoteEventWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    timestamp: Timestamp | timedelta = defaults.timestamp,
    end_timestamp: Timestamp | timedelta = defaults.timestamp,
    note: Note = defaults.note,
    hopo_state: HOPOState = defaults.hopo_state,
    sustain: tuple[int | None, int | None, int | None, int | None, int | None]
    | int = defaults.sustain,
    star_power_data: StarPowerData | None = None,
    _proximal_bpm_event_index: int = defaults.proximal_bpm_event_index,
) -> NoteEvent:
    # TODO(P2): This is probably correct logic, but it would be preferable if it could be more
    # trivially correct. I don't want to write tests for these.
    cs: ComplexSustain
    if isinstance(sustain, tuple):
        cs = SustainTuple(
            (
                Ticks(sustain[0]) if sustain[0] is not None else None,
                Ticks(sustain[1]) if sustain[1] is not None else None,
                Ticks(sustain[2]) if sustain[2] is not None else None,
                Ticks(sustain[3]) if sustain[3] is not None else None,
                Ticks(sustain[4]) if sustain[4] is not None else None,
            )
        )
    elif isinstance(sustain, int):
        cs = Ticks(sustain)
    else:
        raise UnreachableError("unhandled sustain type")

    return NoteEvent(
        tick=Tick(tick),
        timestamp=Timestamp(timestamp),
        end_timestamp=Timestamp(end_timestamp),
        note=note,
        hopo_state=hopo_state,
        sustain=cs,
        star_power_data=star_power_data,
        _proximal_bpm_event_index=_proximal_bpm_event_index,
    )


def NoteEventParsedDataWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    note_track_index: NoteTrackIndex = defaults.note_track_index,
    sustain: Ticks | int = defaults.sustain,
) -> NoteEvent.ParsedData:
    return NoteEvent.ParsedData(
        tick=Tick(tick),
        note_track_index=note_track_index,
        sustain=Ticks(sustain),
    )


def TrackEventWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    timestamp: Timestamp | timedelta = defaults.timestamp,
    value: str = defaults.global_event_value,
    _proximal_bpm_event_index: int = defaults.proximal_bpm_event_index,
) -> TrackEvent:
    return TrackEvent(
        tick=Tick(tick),
        timestamp=Timestamp(timestamp),
        value=value,
        _proximal_bpm_event_index=_proximal_bpm_event_index,
    )


def TrackEventParsedDataWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    value: str = defaults.track_event_value,
) -> TrackEvent.ParsedData:
    return TrackEvent.ParsedData(tick=Tick(tick), value=value)
