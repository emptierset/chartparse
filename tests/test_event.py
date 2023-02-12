from __future__ import annotations

from datetime import timedelta

from chartparse.event import Event
from chartparse.time import Timestamp
from tests.helpers import testcase
from tests.helpers.event import EventWithDefaults


class TestEvent(object):
    class TestStr(object):
        # This just exercises the path; asserting the output is irksome and unnecessary.
        @testcase.parametrize(
            ["event"],
            [
                testcase.new(
                    "integral_timestamp",
                    event=EventWithDefaults(timestamp=Timestamp(timedelta(seconds=1.2))),
                ),
                testcase.new(
                    "nonintegral_timestamp",
                    event=EventWithDefaults(timestamp=Timestamp(timedelta(seconds=1))),
                ),
            ],
        )
        def test(self, event: Event) -> None:
            str(event)
