import pytest

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.synctrack import BPMEvent, TimeSignatureEvent, SyncTrack



class TestSyncTrack(object):
    def test_init(self, basic_sync_track):
        assert basic_sync_track.time_signature_events == pytest.default_time_signature_event_list
        assert basic_sync_track.bpm_events == pytest.default_bpm_event_list

    def test_init_missing_first_time_signature_event(self, mocker, placeholder_string_iterator_getter):
        mocker.patch(
                'chartparse.synctrack.chartparse.track.parse_events_from_iterable',
                return_value=[
                    TimeSignatureEvent(
                        1, pytest.default_upper_time_signature_numeral,
                        pytest.default_lower_time_signature_numeral)])
        with pytest.raises(ValueError):
            _ = SyncTrack(placeholder_string_iterator_getter)

    def test_init_missing_first_bpm_event(self, mocker, placeholder_string_iterator_getter):
        def fake_parse_events_from_iterable(_, from_chart_line_fn):
            event_type = from_chart_line_fn.__self__
            if event_type is TimeSignatureEvent:
                return pytest.default_time_signature_event_list
            elif event_type is BPMEvent:
                return [BPMEvent(1, pytest.default_bpm)]
            else:
                raise ValueError(f"event_type {event_type} not handled")
        mocker.patch(
                'chartparse.synctrack.chartparse.track.parse_events_from_iterable',
                side_effect=fake_parse_events_from_iterable)
        with pytest.raises(ValueError):
            _ = SyncTrack(placeholder_string_iterator_getter)


class TestTimeSignatureEvent(object):
    def test_init(self, time_signature_event):
        assert time_signature_event.upper_numeral == pytest.default_upper_time_signature_numeral
        assert time_signature_event.lower_numeral == pytest.default_lower_time_signature_numeral

    def test_from_chart_line_short(self, generate_valid_short_time_signature_line):
        line = generate_valid_short_time_signature_line()
        event = TimeSignatureEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.upper_numeral == pytest.default_upper_time_signature_numeral

    def test_from_chart_line_long(self, generate_valid_long_time_signature_line):
        line = generate_valid_long_time_signature_line()
        event = TimeSignatureEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.upper_numeral == pytest.default_upper_time_signature_numeral
        assert event.lower_numeral == pytest.default_lower_time_signature_numeral

    def test_from_chart_line_no_match(self, generate_valid_bpm_line):
        line = generate_valid_bpm_line()
        with pytest.raises(RegexFatalNotMatchError):
            _ = TimeSignatureEvent.from_chart_line(line)


class TestBPMEvent(object):
    def test_init(self, bpm_event):
        assert bpm_event.bpm == pytest.default_bpm

    def test_from_chart_line(self, generate_valid_bpm_line):
        line = generate_valid_bpm_line()
        event = BPMEvent.from_chart_line(line)
        assert event.tick == pytest.default_tick
        assert event.bpm == pytest.default_bpm

    def test_from_chart_line_no_match(self, generate_valid_short_time_signature_line):
        line = generate_valid_short_time_signature_line()
        with pytest.raises(RegexFatalNotMatchError):
            _ = BPMEvent.from_chart_line(line)


