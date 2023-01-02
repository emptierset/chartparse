"""parse parses all of the .chart files in the directory that is the first command line arg."""

from glob import glob
import logging
import sys

from chartparse.chart import Chart

logging.basicConfig()
logger = logging.getLogger(__name__)

directory = sys.argv[1]

files = glob(directory + "/*.chart")

logger.setLevel(logging.INFO)

for fname in files:
    logger.info(f"parsing '{fname}'")
    _ = Chart.from_filepath(fname)
