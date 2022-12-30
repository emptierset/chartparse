def generate_bpm(tick, bpm):
    bpm_sans_decimal_point = int(bpm * 1000)
    if bpm_sans_decimal_point != bpm * 1000:
        raise ValueError(f"bpm {bpm} has more than 3 decimal places")
    return f"  {tick} = B {bpm_sans_decimal_point}"


def generate_time_signature(tick, upper, lower=None):
    if lower is not None:
        return f"  {tick} = TS {upper} {lower}"
    else:
        return f"  {tick} = TS {upper}"


# TODO: Rename the functions in here to remove the _event suffix.
def generate_anchor_event(tick, microseconds):
    return f"  {tick} = A {microseconds}"


def generate_text_event(tick, value):
    return f'  {tick} = E "{value}"'


def generate_section_event(tick, value):
    return f'  {tick} = E "section {value}"'


def generate_lyric_event(tick, value):
    return f'  {tick} = E "lyric {value}"'


def generate_note(tick, note, sustain=0):
    return f"  {tick} = N {note} {sustain}"


def generate_star_power(tick, sustain):
    return f"  {tick} = S 2 {sustain}"


def generate_track(tick, value):
    return f"  {tick} = E {value}"
