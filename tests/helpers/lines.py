from chartparse.instrument import NoteTrackIndex
from chartparse.tick import Tick, Ticks


def generate_bpm_line(tick: Tick, bpm: float) -> str:
    bpm_sans_decimal_point = int(bpm * 1000)
    if bpm_sans_decimal_point != bpm * 1000:
        raise ValueError(f"bpm {bpm} has more than 3 decimal places")
    return f"  {tick} = B {bpm_sans_decimal_point}"


def generate_time_signature_line(tick: Tick, upper: int, lower: int | None = None) -> str:
    if lower is not None:
        return f"  {tick} = TS {upper} {lower}"
    else:
        return f"  {tick} = TS {upper}"


def generate_anchor_line(tick: Tick, microseconds: int) -> str:
    return f"  {tick} = A {microseconds}"


def generate_text_line(tick: Tick, value: str) -> str:
    return f'  {tick} = E "{value}"'


def generate_section_line(tick: Tick, value: str) -> str:
    return f'  {tick} = E "section {value}"'


def generate_lyric_line(tick: Tick, value: str) -> str:
    return f'  {tick} = E "lyric {value}"'


def generate_note_line(tick: Tick, note: NoteTrackIndex, sustain: Ticks = Ticks(0)) -> str:
    return f"  {tick} = N {note.value} {sustain}"


def generate_star_power_line(tick: Tick, sustain: Ticks) -> str:
    return f"  {tick} = S 2 {sustain}"


def generate_track_line(tick: Tick, value: str) -> str:
    return f"  {tick} = E {value}"
