from __future__ import annotations

from datetime import timedelta

import chartparse.time
from chartparse.time import Seconds, Timestamp
from tests.helpers import testcase


class TestAdd(object):
    @testcase.parametrize(
        ["ts", "other", "want"],
        [
            testcase.new(
                "seconds",
                ts=timedelta(seconds=2.2),
                other=Seconds(1.5),
                want=timedelta(seconds=3.7),
            ),
            testcase.new(
                "timedelta",
                ts=timedelta(seconds=2.3),
                other=timedelta(seconds=1.6),
                want=timedelta(seconds=3.9),
            ),
        ],
    )
    def test(self, ts: timedelta, other: timedelta | Seconds, want: timedelta) -> None:
        got = chartparse.time.add(Timestamp(ts), other)
        assert got == Timestamp(want)
