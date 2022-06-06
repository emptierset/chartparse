import chartparse.track
from chartparse.event import EventsEvent
from chartparse.util import DictPropertiesEqMixin


class Events(DictPropertiesEqMixin):
    def __init__(self, iterator_getter):
        self.events = chartparse.track.parse_events_from_iterable(
            iterator_getter(), EventsEvent.from_chart_line
        )
