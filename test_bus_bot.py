import datetime
from unittest.mock import Mock, patch

import pytest

from bus_bot import (
    weekday_trips,
    saturday_trips,
    weekday_breaks,
    get_stop_schedule,
    get_day_type,
    get_trips_for_day_type,
    add_minutes,
    minutes_until,
    build_next_bus_text,
    build_schedule_text,
    handle_location_callback,
    handle_schedule_callback,
    prompt_location,
    prompt_schedule,
    format_asr_schedule,
    format_stop_schedule,
    STOP_NAMES,
    STOP_OFFSETS,
    SG_HOLIDAYS,
)



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
    @patch("bus_bot.get_singapore_now")
    def test_weekday_detection(self, mock_now, day):
        mock_now.return_value = datetime.datetime(2026, 1, 5 + day, 10, 0, tzinfo=datetime.timezone.utc)
        assert get_day_type() == "weekday"

    @patch("bus_bot.get_singapore_now")
    def test_saturday_detection(self, mock_now):
        mock_now.return_value = datetime.datetime(2026, 1, 10, 10, 0, tzinfo=datetime.timezone.utc)
        assert get_day_type() == "saturday"

    @patch("bus_bot.get_singapore_now")
    def test_sunday_detection(self, mock_now):
        mock_now.return_value = datetime.datetime(2026, 1, 11, 10, 0, tzinfo=datetime.timezone.utc)
        assert get_day_type() == "sunday"

    def test_get_trips_weekday(self):
        assert get_trips_for_day_type("weekday") is weekday_trips

    def test_get_trips_saturday(self):
        assert get_trips_for_day_type("saturday") is saturday_trips

    def test_get_trips_sunday(self):
        assert get_trips_for_day_type("sunday") is None



class TestPublicHoliday:

    @patch("bus_bot.get_singapore_now")
    def test_weekday_public_holiday_returns_saturday(self, mock_now):
        """2026-01-01 (New Year's Day) is a Thursday — should return saturday."""
        mock_now.return_value = datetime.datetime(2026, 1, 1, 10, 0, tzinfo=datetime.timezone.utc)
        assert get_day_type() == "saturday"

    @patch("bus_bot.get_singapore_now")
    def test_sunday_public_holiday_returns_sunday(self, mock_now):
        """2026-08-09 (National Day) is a Sunday — should still return sunday."""
        mock_now.return_value = datetime.datetime(2026, 8, 9, 10, 0, tzinfo=datetime.timezone.utc)
        assert get_day_type() == "sunday"

    @patch("bus_bot.get_singapore_now")
    def test_saturday_public_holiday_returns_saturday(self, mock_now):
        """2028-01-01 (New Year's Day) is a Saturday."""
        mock_now.return_value = datetime.datetime(2028, 1, 1, 10, 0, tzinfo=datetime.timezone.utc)
        assert get_day_type() == "saturday"

    @patch("bus_bot.get_singapore_now")
    def test_normal_weekday_not_holiday(self, mock_now):
        """2026-01-05 (Monday, not a holiday) — should return weekday."""
        mock_now.return_value = datetime.datetime(2026, 1, 5, 10, 0, tzinfo=datetime.timezone.utc)
        assert get_day_type() == "weekday"

    def test_sg_holidays_contains_known_dates(self):
        assert datetime.date(2026, 1, 1) in SG_HOLIDAYS
        assert datetime.date(2026, 8, 9) in SG_HOLIDAYS



class TestBuildNextBusText:

    @patch("bus_bot.get_singapore_now")
    def test_next_bus_asr_morning(self, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 25)))
        text = build_next_bus_text("asr", "weekday")
        assert "min" in text
        assert "Going to" in text

    @patch("bus_bot.get_singapore_now")
    def test_all_buses_passed(self, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(21, 0)))
        text = build_next_bus_text("asr", "weekday")
        assert "no more bus" in text.lower()

    @patch("bus_bot.get_singapore_now")
    def test_next_bus_harbourfront(self, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(10, 5)))
        text = build_next_bus_text("harbourfront", "weekday")
        assert "min" in text



class TestLocationInlineKeyboard:

    def setup_method(self):
        self.mock_update = Mock()
        self.mock_context = Mock()

    @patch("bus_bot.get_day_type", return_value="weekday")
    def test_prompt_location_sends_inline_keyboard(self, _):
        self.mock_update.message.reply_text = Mock()
        prompt_location(self.mock_update, self.mock_context)
        call_kwargs = self.mock_update.message.reply_text.call_args[1]
        reply_markup = call_kwargs.get("reply_markup")
        assert reply_markup is not None
        buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
        assert len(buttons) == len(STOP_NAMES)
        callback_data = [btn.callback_data for btn in buttons]
        for stop_key in STOP_NAMES:
            assert f"location:{stop_key}" in callback_data

    @patch("bus_bot.get_day_type", return_value="sunday")
    def test_prompt_location_sunday_no_service(self, _):
        self.mock_update.message.reply_text = Mock()
        prompt_location(self.mock_update, self.mock_context)
        msg = self.mock_update.message.reply_text.call_args[0][0]
        assert "sunday no bus lah" in msg.lower()

    @patch("bus_bot.get_singapore_now")
    @patch("bus_bot.get_day_type", return_value="weekday")
    def test_handle_location_callback_edits_message(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 25)))
        query = Mock()
        query.data = "location:asr"
        self.mock_update.callback_query = query
        handle_location_callback(self.mock_update, self.mock_context)
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        text = query.edit_message_text.call_args[0][0]
        assert "min" in text

    @patch("bus_bot.get_day_type", return_value="sunday")
    def test_handle_location_callback_sunday(self, _):
        query = Mock()
        query.data = "location:asr"
        self.mock_update.callback_query = query
        handle_location_callback(self.mock_update, self.mock_context)
        text = query.edit_message_text.call_args[0][0]
        assert "sunday no bus lah" in text.lower()

    @patch("bus_bot.get_singapore_now")
    @patch("bus_bot.get_day_type", return_value="weekday")
    def test_handle_location_callback_keeps_inline_keyboard(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        query = Mock()
        query.data = "location:outram_exit_6"
        self.mock_update.callback_query = query
        handle_location_callback(self.mock_update, self.mock_context)
        call_kwargs = query.edit_message_text.call_args[1]
        assert "reply_markup" in call_kwargs



class TestBuildScheduleText:

    def test_asr_weekday_schedule(self):
        text = build_schedule_text("asr", "weekday")
        assert "07:20" in text
        assert "Outram Park MRT" in text
        assert "Harbourfront MRT Exit D" in text
        assert "Weekday" in text

    def test_harbourfront_weekday_schedule(self):
        text = build_schedule_text("harbourfront", "weekday")
        assert "Harbourfront MRT Exit D" in text
        assert "07:20" not in text

    def test_saturday_schedule(self):
        text = build_schedule_text("asr", "saturday")
        assert "Saturday" in text
        assert "09:00" in text



class TestScheduleInlineKeyboard:

    def setup_method(self):
        self.mock_update = Mock()
        self.mock_context = Mock()

    @patch("bus_bot.get_day_type", return_value="weekday")
    def test_prompt_schedule_sends_inline_keyboard(self, _):
        self.mock_update.message.reply_text = Mock()
        prompt_schedule(self.mock_update, self.mock_context)
        call_kwargs = self.mock_update.message.reply_text.call_args[1]
        reply_markup = call_kwargs.get("reply_markup")
        assert reply_markup is not None
        buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
        assert len(buttons) == len(STOP_NAMES)
        callback_data = [btn.callback_data for btn in buttons]
        for stop_key in STOP_NAMES:
            assert f"schedule:{stop_key}" in callback_data

    @patch("bus_bot.get_day_type", return_value="sunday")
    def test_prompt_schedule_sunday_message(self, _):
        self.mock_update.message.reply_text = Mock()
        prompt_schedule(self.mock_update, self.mock_context)
        msg = self.mock_update.message.reply_text.call_args[0][0]
        assert "Sunday no bus lah" in msg

    @patch("bus_bot.get_day_type", return_value="weekday")
    def test_handle_schedule_callback_edits_message(self, _):
        query = Mock()
        query.data = "schedule:asr"
        self.mock_update.callback_query = query
        handle_schedule_callback(self.mock_update, self.mock_context)
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        text = query.edit_message_text.call_args[0][0]
        assert "07:20" in text
        assert "Weekday" in text

    @patch("bus_bot.get_day_type", return_value="sunday")
    def test_handle_schedule_callback_sunday_shows_weekday(self, _):
        query = Mock()
        query.data = "schedule:asr"
        self.mock_update.callback_query = query
        handle_schedule_callback(self.mock_update, self.mock_context)
        text = query.edit_message_text.call_args[0][0]
        assert "Weekday" in text

    @patch("bus_bot.get_day_type", return_value="weekday")
    def test_handle_schedule_callback_keeps_inline_keyboard(self, _):
        query = Mock()
        query.data = "schedule:harbourfront"
        self.mock_update.callback_query = query
        handle_schedule_callback(self.mock_update, self.mock_context)
        call_kwargs = query.edit_message_text.call_args[1]
        assert "reply_markup" in call_kwargs



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
            "07:26", "07:46", "08:06", "08:26", "08:46", "09:06",
            "09:36", "10:36", "11:36",
            "13:36", "14:36",
            "16:36", "17:36", "18:36", "19:36",
        ]
        assert times == expected

    def test_weekday_outram_exit_7_times(self):
        times = self.times(get_stop_schedule(weekday_trips, "outram_exit_7"))
        expected = [
            "07:28", "07:48", "08:08", "08:28", "08:48", "09:08",
            "09:38", "10:38", "11:38",
            "13:38", "14:38",
            "16:38", "17:38", "18:38", "19:38",
        ]
        assert times == expected

    def test_weekday_harbourfront_times(self):
        times = self.times(get_stop_schedule(weekday_trips, "harbourfront"))
        expected = [
            "10:10", "11:10",
            "13:10", "14:10", "15:10",
            "17:10", "18:10", "19:10", "20:10",
        ]
        assert times == expected

    def test_saturday_outram_exit_6_times(self):
        times = self.times(get_stop_schedule(saturday_trips, "outram_exit_6"))
        expected = [
            "09:06", "10:06", "11:06", "12:06",
            "14:06", "15:06", "16:06",
            "18:06", "19:06", "20:06",
        ]
        assert times == expected

    def test_saturday_outram_exit_7_times(self):
        times = self.times(get_stop_schedule(saturday_trips, "outram_exit_7"))
        expected = [
            "09:08", "10:08", "11:08", "12:08",
            "14:08", "15:08", "16:08",
            "18:08", "19:08", "20:08",
        ]
        assert times == expected

    def test_saturday_harbourfront_times(self):
        times = self.times(get_stop_schedule(saturday_trips, "harbourfront"))
        expected = [
            "09:40", "10:40", "11:40", "12:40",
            "14:40", "15:40", "16:40",
            "18:40", "19:40", "20:40",
        ]
        assert times == expected

    def test_saturday_asr_times(self):
        times = self.times(get_stop_schedule(saturday_trips, "asr"))
        expected = [
            "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
            "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
            "18:00", "18:30", "19:00", "19:30", "20:00", "20:30",
        ]
        assert times == expected



class TestNextBusEdgeCases:

    @patch("bus_bot.get_singapore_now")
    def test_during_lunch_break_finds_next_trip(self, mock_now):
        """At 12:30 (weekday lunch break 12:00-13:00), next ASR bus is 13:00."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(12, 30)))
        text = build_next_bus_text("asr", "weekday")
        assert "30 min" in text
        assert "13:00" in text

    @patch("bus_bot.get_singapore_now")
    def test_last_bus_no_following(self, mock_now):
        """At 19:55, next ASR bus is 20:00 (last one) — no following bus."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(19, 55)))
        text = build_next_bus_text("asr", "weekday")
        assert "5 min" in text
        assert "last bus already" in text.lower()

    @patch("bus_bot.get_singapore_now")
    def test_next_bus_shows_following(self, mock_now):
        """At 07:00, next bus is 07:20 and following is 07:40 — both shown."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        text = build_next_bus_text("asr", "weekday")
        assert "07:20" in text
        assert "07:40" in text

    @patch("bus_bot.get_singapore_now")
    def test_saturday_next_bus(self, mock_now):
        """Saturday at 09:15, next ASR bus should be 09:30 (type B → Harbourfront)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(9, 15)))
        text = build_next_bus_text("asr", "saturday")
        assert "15 min" in text
        assert "Harbourfront" in text

    @patch("bus_bot.get_singapore_now")
    def test_saturday_all_buses_passed(self, mock_now):
        """Saturday at 21:00, all buses should have passed."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(21, 0)))
        text = build_next_bus_text("outram_exit_6", "saturday")
        assert "no more bus" in text.lower()

    @patch("bus_bot.get_singapore_now")
    def test_harbourfront_during_morning_no_service(self, mock_now):
        """Weekday at 08:30, no Harbourfront buses yet (first is 10:10)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(8, 30)))
        text = build_next_bus_text("harbourfront", "weekday")
        assert "10:10" in text

    @patch("bus_bot.get_singapore_now")
    def test_asr_destination_alternates(self, mock_now):
        """At 09:25, next ASR bus is 09:30 (A→Outram), following is 10:00 (B→Harbourfront)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(9, 25)))
        text = build_next_bus_text("asr", "weekday")
        assert "Outram Park MRT" in text
        assert "Harbourfront MRT Exit D" in text

    @patch("bus_bot.get_singapore_now")
    def test_exact_departure_time_still_shown(self, mock_now):
        """At exactly 07:20, the 07:20 bus should still be shown (0 min)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 20)))
        text = build_next_bus_text("asr", "weekday")
        assert "07:20" in text
        assert "0 min" in text

    @patch("bus_bot.get_singapore_now")
    def test_exact_last_bus_time(self, mock_now):
        """At exactly 20:00, the last bus should still be shown, not 'all passed'."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(20, 0)))
        text = build_next_bus_text("asr", "weekday")
        assert "20:00" in text
        assert "no more bus" not in text.lower()
