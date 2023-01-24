"""parse parses all of the .chart files in the directory that is the first command line arg."""

import logging
import pathlib
import sys
import timeit
from glob import glob

from chartparse.chart import Chart
from chartparse.instrument import Difficulty, Instrument

logging.basicConfig()
logger = logging.getLogger(__name__)

directory = sys.argv[1]

fpaths = [pathlib.Path(fname) for fname in glob(directory + "/*.chart")]

logger.setLevel(logging.INFO)

start_time = timeit.default_timer()

for fpath in fpaths:
    logger.info(f"parsing '{fpath}'")
    _ = Chart.from_filepath(fpath, want_tracks=[(Instrument.GUITAR, Difficulty.EXPERT)])

elapsed = timeit.default_timer() - start_time
logger.info(f"finished in {elapsed} seconds")
