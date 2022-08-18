import datetime
import pytest

from chartparse.event import Event


class TestEvent(object):
    class TestInit(object):
        def test_basic(self, tick_having_event):
            assert tick_having_event.tick == pytest.defaults.tick

    class TestCalculateTimestamp(object):
        nonzero_timedelta = datetime.timedelta(1)
        nonzero_int = 1

        def test_early_return(self, minimal_timestamp_getter):
            got_timestamp, got_proximal_bpm_event_idx = Event.calculate_timestamp(
                pytest.defaults.tick, None, minimal_timestamp_getter, pytest.defaults.resolution
            )
            assert got_timestamp == datetime.timedelta(0)
            assert got_proximal_bpm_event_idx == 0

        @pytest.mark.parametrize(
            "prev_event_proximal_bpm_event_idx,want_called_start_bpm_event_index",
            [(None, 0), (1, 1)],
        )
        def test_callback(
            self, mocker, prev_event_proximal_bpm_event_idx, want_called_start_bpm_event_index
        ):
            prev_event = Event(
                pytest.defaults.tick,
                pytest.defaults.timestamp,
                proximal_bpm_event_idx=prev_event_proximal_bpm_event_idx,
            )
            stub = mocker.stub(name="timestamp_getter")
            Event.calculate_timestamp(
                pytest.defaults.tick, prev_event, stub, pytest.defaults.resolution
            )
            stub.assert_called_once_with(
                pytest.defaults.tick,
                pytest.defaults.resolution,
                start_bpm_event_index=want_called_start_bpm_event_index,
            )
