import datetime
from unittest.mock import patch

import pytest

from config import SG_HOLIDAYS, STOP_OFFSETS, saturday_trips, weekday_breaks, weekday_trips
from helpers import (
    add_minutes,
    format_asr_schedule,
    format_stop_schedule,
    get_day_type,
    get_stop_schedule,
    get_trips_for_day_type,
    minutes_until,
)


class TestHelpers:
    def test_add_minutes(self):
        assert add_minutes("07:20", 6) == "07:26"
        assert add_minutes("07:20", 8) == "07:28"
        assert add_minutes("23:55", 10) == "00:05"

    def test_get_stop_schedule_asr(self):
        schedule = get_stop_schedule(weekday_trips, "asr")
        assert len(schedule) == 24
        assert schedule[0] == ("07:20", "A")

    def test_get_stop_schedule_outram_exit_6(self):
        schedule = get_stop_schedule(weekday_trips, "outram_exit_6")
        assert schedule[0][0] == "07:26"
        for time_str, _ in schedule:
            assert len(time_str) == 5 and time_str[2] == ":"

    def test_get_stop_schedule_outram_exit_7(self):
        schedule = get_stop_schedule(weekday_trips, "outram_exit_7")
        assert schedule[0][0] == "07:28"

    def test_get_stop_schedule_harbourfront(self):
        schedule = get_stop_schedule(weekday_trips, "harbourfront")
        b_count = sum(1 for _, t in weekday_trips if t == "B")
        assert len(schedule) == b_count

    @pytest.mark.parametrize("trips", [weekday_trips, saturday_trips])
    def test_outram_stops_only_on_type_a(self, trips):
        schedule = get_stop_schedule(trips, "outram_exit_6")
        for _, trip_type in schedule:
            assert trip_type == "A"

    @pytest.mark.parametrize("trips", [weekday_trips, saturday_trips])
    def test_harbourfront_only_on_type_b(self, trips):
        schedule = get_stop_schedule(trips, "harbourfront")
        for _, trip_type in schedule:
            assert trip_type == "B"

    def test_minutes_until(self):
        assert minutes_until(datetime.time(7, 0), datetime.time(7, 20)) == 20
        assert minutes_until(datetime.time(12, 30), datetime.time(13, 0)) == 30

    def test_stop_offsets(self):
        assert STOP_OFFSETS["asr"] == 0
        assert STOP_OFFSETS["outram_exit_6"] == 6
        assert STOP_OFFSETS["outram_exit_7"] == 8
        assert STOP_OFFSETS["harbourfront"] == 10

    @pytest.mark.parametrize("trips", [weekday_trips, saturday_trips])
    def test_per_stop_chronological_order(self, trips):
        for stop_key in STOP_OFFSETS:
            schedule = get_stop_schedule(trips, stop_key)
            prev = None
            for time_str, _ in schedule:
                t = datetime.datetime.strptime(time_str, "%H:%M").time()
                if prev:
                    assert t > prev, f"{stop_key} out of order at {time_str}"
                prev = t


class TestDayType:
    @pytest.mark.parametrize("day", range(5))
    @patch("helpers.get_singapore_now")
    def test_weekday_detection(self, mock_now, day):
        mock_now.return_value = datetime.datetime(2026, 1, 5 + day, 10, 0, tzinfo=datetime.UTC)
        assert get_day_type() == "weekday"

    @patch("helpers.get_singapore_now")
    def test_saturday_detection(self, mock_now):
        mock_now.return_value = datetime.datetime(2026, 1, 10, 10, 0, tzinfo=datetime.UTC)
        assert get_day_type() == "saturday"

    @patch("helpers.get_singapore_now")
    def test_sunday_detection(self, mock_now):
        mock_now.return_value = datetime.datetime(2026, 1, 11, 10, 0, tzinfo=datetime.UTC)
        assert get_day_type() == "sunday"

    def test_get_trips_weekday(self):
        assert get_trips_for_day_type("weekday") is weekday_trips

    def test_get_trips_saturday(self):
        assert get_trips_for_day_type("saturday") is saturday_trips

    def test_get_trips_sunday(self):
        assert get_trips_for_day_type("sunday") is None


class TestPublicHoliday:
    @patch("helpers.get_singapore_now")
    def test_weekday_public_holiday_returns_saturday(self, mock_now):
        """2026-01-01 (New Year's Day) is a Thursday — should return saturday."""
        mock_now.return_value = datetime.datetime(2026, 1, 1, 10, 0, tzinfo=datetime.UTC)
        assert get_day_type() == "saturday"

    @patch("helpers.get_singapore_now")
    def test_sunday_public_holiday_returns_sunday(self, mock_now):
        """2026-08-09 (National Day) is a Sunday — should still return sunday."""
        mock_now.return_value = datetime.datetime(2026, 8, 9, 10, 0, tzinfo=datetime.UTC)
        assert get_day_type() == "sunday"

    @patch("helpers.get_singapore_now")
    def test_saturday_public_holiday_returns_saturday(self, mock_now):
        """2028-01-01 (New Year's Day) is a Saturday."""
        mock_now.return_value = datetime.datetime(2028, 1, 1, 10, 0, tzinfo=datetime.UTC)
        assert get_day_type() == "saturday"

    @patch("helpers.get_singapore_now")
    def test_normal_weekday_not_holiday(self, mock_now):
        """2026-01-05 (Monday, not a holiday) — should return weekday."""
        mock_now.return_value = datetime.datetime(2026, 1, 5, 10, 0, tzinfo=datetime.UTC)
        assert get_day_type() == "weekday"

    def test_sg_holidays_contains_known_dates(self):
        assert datetime.date(2026, 1, 1) in SG_HOLIDAYS
        assert datetime.date(2026, 8, 9) in SG_HOLIDAYS


class TestFormatting:
    def test_asr_schedule_contains_breaks(self):
        text = format_asr_schedule(weekday_trips, weekday_breaks, "20:15")
        assert "Driver Break" in text
        assert "Lunch Break" in text
        assert "Last drop-off: 20:15" in text

    def test_asr_schedule_contains_destinations(self):
        text = format_asr_schedule(weekday_trips, weekday_breaks, "20:15")
        assert "→ Outram Park MRT" in text
        assert "→ Harbourfront MRT Exit D" in text

    def test_stop_schedule_format(self):
        text = format_stop_schedule(weekday_trips, "outram_exit_6", weekday_breaks)
        assert "07:26" in text
        assert "→" not in text


class TestScheduleAccuracy:
    @staticmethod
    def times(schedule):
        return [t for t, _ in schedule]

    def test_weekday_outram_exit_6_times(self):
        times = self.times(get_stop_schedule(weekday_trips, "outram_exit_6"))
        expected = [
            "07:26",
            "07:46",
            "08:06",
            "08:26",
            "08:46",
            "09:06",
            "09:36",
            "10:36",
            "11:36",
            "13:36",
            "14:36",
            "16:36",
            "17:36",
            "18:36",
            "19:36",
        ]
        assert times == expected

    def test_weekday_outram_exit_7_times(self):
        times = self.times(get_stop_schedule(weekday_trips, "outram_exit_7"))
        expected = [
            "07:28",
            "07:48",
            "08:08",
            "08:28",
            "08:48",
            "09:08",
            "09:38",
            "10:38",
            "11:38",
            "13:38",
            "14:38",
            "16:38",
            "17:38",
            "18:38",
            "19:38",
        ]
        assert times == expected

    def test_weekday_harbourfront_times(self):
        times = self.times(get_stop_schedule(weekday_trips, "harbourfront"))
        expected = [
            "10:10",
            "11:10",
            "13:10",
            "14:10",
            "15:10",
            "17:10",
            "18:10",
            "19:10",
            "20:10",
        ]
        assert times == expected

    def test_saturday_outram_exit_6_times(self):
        times = self.times(get_stop_schedule(saturday_trips, "outram_exit_6"))
        expected = [
            "09:06",
            "10:06",
            "11:06",
            "12:06",
            "14:06",
            "15:06",
            "16:06",
            "18:06",
            "19:06",
            "20:06",
        ]
        assert times == expected

    def test_saturday_outram_exit_7_times(self):
        times = self.times(get_stop_schedule(saturday_trips, "outram_exit_7"))
        expected = [
            "09:08",
            "10:08",
            "11:08",
            "12:08",
            "14:08",
            "15:08",
            "16:08",
            "18:08",
            "19:08",
            "20:08",
        ]
        assert times == expected

    def test_saturday_harbourfront_times(self):
        times = self.times(get_stop_schedule(saturday_trips, "harbourfront"))
        expected = [
            "09:40",
            "10:40",
            "11:40",
            "12:40",
            "14:40",
            "15:40",
            "16:40",
            "18:40",
            "19:40",
            "20:40",
        ]
        assert times == expected

    def test_saturday_asr_times(self):
        times = self.times(get_stop_schedule(saturday_trips, "asr"))
        expected = [
            "09:00",
            "09:30",
            "10:00",
            "10:30",
            "11:00",
            "11:30",
            "12:00",
            "12:30",
            "14:00",
            "14:30",
            "15:00",
            "15:30",
            "16:00",
            "16:30",
            "18:00",
            "18:30",
            "19:00",
            "19:30",
            "20:00",
            "20:30",
        ]
        assert times == expected
