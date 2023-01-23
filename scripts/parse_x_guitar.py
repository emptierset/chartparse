"""parse parses all of the .chart files in the directory that is the first command line arg."""

from glob import glob
import logging
import sys
import timeit

from chartparse.chart import Chart
from chartparse.instrument import Instrument,Difficulty

logging.basicConfig()
logger = logging.getLogger(__name__)

directory = sys.argv[1]

files = glob(directory + "/*.chart")

logger.setLevel(logging.INFO)

start_time = timeit.default_timer()

for fname in files:
    logger.info(f"parsing '{fname}'")
    _ = Chart.from_filepath(fname, want_tracks=[(Instrument.GUITAR, Difficulty.EXPERT)])

elapsed = timeit.default_timer() - start_time
logger.info(f"finished in {elapsed} seconds")
