from __future__ import annotations

from datetime import timedelta

from tests.helpers import testcase
from tests.helpers.event import EventWithDefaults

# TODO: typecheck the tests in this file by adding "-> None" annotations to each test function.

class TestEvent(object):
    class TestStr(object):
        # This just exercises the path; asserting the output is irksome and unnecessary.
        @testcase.parametrize(
            ["event"],
            [
                testcase.new(
                    "integral_timestamp",
                    event=EventWithDefaults(timestamp=timedelta(seconds=1.2)),
                ),
                testcase.new(
                    "nonintegral_timestamp",
                    event=EventWithDefaults(timestamp=timedelta(seconds=1)),
                ),
            ],
        )
        def test(self, event):
            str(event)
