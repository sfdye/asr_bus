import datetime

import pytest

from config import saturday_trips, weekday_trips


class TestTripData:
    def test_weekday_trip_count(self):
        assert len(weekday_trips) == 24

    def test_saturday_trip_count(self):
        assert len(saturday_trips) == 20

    @pytest.mark.parametrize("trips", [weekday_trips, saturday_trips])
    def test_time_format(self, trips):
        for time_str, trip_type in trips:
            assert len(time_str) == 5 and time_str[2] == ":"
            assert trip_type in ("A", "B")

    @pytest.mark.parametrize("trips", [weekday_trips, saturday_trips])
    def test_chronological_order(self, trips):
        prev = None
        for time_str, _ in trips:
            t = datetime.datetime.strptime(time_str, "%H:%M").time()
            if prev:
                assert t > prev, f"Out of order at {time_str}"
            prev = t

    def test_weekday_trip_type_counts(self):
        a_count = sum(1 for _, t in weekday_trips if t == "A")
        b_count = sum(1 for _, t in weekday_trips if t == "B")
        assert a_count == 15
        assert b_count == 9

    def test_saturday_trip_type_counts(self):
        a_count = sum(1 for _, t in saturday_trips if t == "A")
        b_count = sum(1 for _, t in saturday_trips if t == "B")
        assert a_count == 10
        assert b_count == 10

    def test_weekday_first_last(self):
        assert weekday_trips[0] == ("07:20", "A")
        assert weekday_trips[-1] == ("20:00", "B")

    def test_saturday_first_last(self):
        assert saturday_trips[0] == ("09:00", "A")
        assert saturday_trips[-1] == ("20:30", "B")
