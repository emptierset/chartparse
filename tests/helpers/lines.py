import math


def generate_bpm(tick, bpm):
    bpm_sans_decimal_point = int(bpm * 1000)
    if bpm_sans_decimal_point != bpm * 1000:
        raise ValueError(f"bpm {bpm} has more than 3 decimal places")
    return f"  {tick} = B {bpm_sans_decimal_point}"


def generate_time_signature(tick, upper_numeral, lower_numeral=None):
    if lower_numeral is not None:
        lg_base2_of_lower = math.log(lower_numeral, 2)
        if int(lg_base2_of_lower) != lg_base2_of_lower:
            raise ValueError(f"lower_numeral {lower_numeral} is not a power of 2")
        return f"  {tick} = TS {upper_numeral} {int(lg_base2_of_lower)}"
    else:
        return f"  {tick} = TS {upper_numeral}"


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
