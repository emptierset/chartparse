import datetime
import pytest

from chartparse.event import Event


class TestEvent(object):
    class TestInit(object):
        def test(self, tick_having_event):
            assert tick_having_event.tick == pytest.defaults.tick

    class TestCalculateTimestamp(object):
        nonzero_timedelta = datetime.timedelta(1)
        nonzero_int = 1

        def test_early_return(self, minimal_tatter):
            got_timestamp, got_proximal_bpm_event_idx = Event.calculate_timestamp(
                pytest.defaults.tick, None, minimal_tatter
            )
            assert got_timestamp == datetime.timedelta(0)
            assert got_proximal_bpm_event_idx == 0

        @pytest.mark.parametrize(
            "prev_event_proximal_bpm_event_idx,want_called_start_bpm_event_index",
            [(None, 0), (1, 1)],
        )
        def test_callback(
            self,
            mocker,
            minimal_tatter,
            prev_event_proximal_bpm_event_idx,
            want_called_start_bpm_event_index,
        ):
            prev_event = Event(
                pytest.defaults.tick,
                pytest.defaults.timestamp,
                proximal_bpm_event_idx=prev_event_proximal_bpm_event_idx,
            )
            spy_timestamp_at_tick = mocker.spy(minimal_tatter, "timestamp_at_tick")
            Event.calculate_timestamp(pytest.defaults.tick, prev_event, minimal_tatter)
            spy_timestamp_at_tick.assert_called_once_with(
                pytest.defaults.tick,
                start_bpm_event_index=want_called_start_bpm_event_index,
            )
