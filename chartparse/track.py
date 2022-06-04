from chartparse.exceptions import RegexFatalNotMatchError


def parse_events_from_iterable(iterable, from_chart_line_fn):
    events = []
    for line in iterable:
        try:
            event = from_chart_line_fn(line)
        except RegexFatalNotMatchError:
            continue
        events.append(event)
    events.sort(key=lambda e: e.tick)
    return events
