---
# chartparse

[![codecov](https://codecov.io/gh/AWConant/chartparse/branch/main/graph/badge.svg?token=chartparse_token_here)](https://codecov.io/gh/AWConant/chartparse)
[![CI](https://github.com/AWConant/chartparse/actions/workflows/main.yml/badge.svg)](https://github.com/AWConant/chartparse/actions/workflows/main.yml)

## Install it from PyPI

```bash
pip install chartparse
```

## Usage

```py
from chartparse.chart import Chart
from chartparse.enums import Instrument, Difficulty

with open("/path/to/file.chart", "r", encoding="utf-8-sig") as f:
	c = Chart(f)

# the first 7 BPM changes
c.sync_track.bpm_events[:7]

# the first 8 time signature changes
c.sync_track.time_signature_events[:8]

expert_guitar = c.instrument_tracks[Instrument.GUITAR][Difficulty.EXPERT]

# the first 10 notes of the expert guitar chart
expert_guitar.note_events[:10]

# the first 3 star power phrases of the expert guitar chart
expert_guitar.star_power_events[:3]
```

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.
