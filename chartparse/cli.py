import sys

from chartparse.chart import Chart
from chartparse.enums import Difficulty, Instrument


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m chartparse <path_to_chart_file>")
        sys.exit(1)

    infile_name = sys.argv[1]
    with open(infile_name, "r", encoding="utf-8-sig") as f:
        c = Chart(f)

    print(c.properties)
    expert_guitar = c.instrument_tracks[Instrument.GUITAR][Difficulty.EXPERT]
    print(expert_guitar)
    for e in expert_guitar.note_events[:10]:
        print(e)
    for e in c.sync_track.time_signature_events[:5]:
        print(e)
    for e in c.sync_track.bpm_events[:10]:
        print(e)
    for e in c.events_track.events[:5]:
        print(e)


if __name__ == "__main__":
    main()
