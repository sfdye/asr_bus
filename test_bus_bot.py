import unittest
import datetime
from unittest.mock import Mock, patch

from bus_bot import (
    weekday_trips,
    saturday_trips,
    weekday_breaks,
    get_stop_schedule,
    get_day_type,
    get_trips_for_day_type,
    add_minutes,
    minutes_until,
    next_bus_time,
    get_schedule,
    prompt_location,
    format_asr_schedule,
    format_stop_schedule,
    STOP_OFFSETS,
    TRIP_DESTINATIONS,
    SCHEDULE_BUTTONS,
    SCHEDULE_BUTTON_MAP,
    LOCATION_BUTTONS,
    LOCATION_BUTTON_MAP,
)


class TestTripData(unittest.TestCase):

    def test_weekday_trip_count(self):
        self.assertEqual(len(weekday_trips), 23)

    def test_saturday_trip_count(self):
        self.assertEqual(len(saturday_trips), 20)

    def test_time_format(self):
        for trips in [weekday_trips, saturday_trips]:
            for time_str, trip_type in trips:
                self.assertRegex(time_str, r'^\d{2}:\d{2}$')
                self.assertIn(trip_type, ("A", "B"))

    def test_chronological_order(self):
        for trips in [weekday_trips, saturday_trips]:
            prev = None
            for time_str, _ in trips:
                t = datetime.datetime.strptime(time_str, "%H:%M").time()
                if prev:
                    self.assertGreater(t, prev, f"Out of order at {time_str}")
                prev = t

    def test_weekday_trip_type_counts(self):
        a_count = sum(1 for _, t in weekday_trips if t == "A")
        b_count = sum(1 for _, t in weekday_trips if t == "B")
        self.assertEqual(a_count, 14)
        self.assertEqual(b_count, 9)

    def test_saturday_trip_type_counts(self):
        a_count = sum(1 for _, t in saturday_trips if t == "A")
        b_count = sum(1 for _, t in saturday_trips if t == "B")
        self.assertEqual(a_count, 10)
        self.assertEqual(b_count, 10)

    def test_weekday_first_last(self):
        self.assertEqual(weekday_trips[0], ("07:20", "A"))
        self.assertEqual(weekday_trips[-1], ("20:00", "B"))

    def test_saturday_first_last(self):
        self.assertEqual(saturday_trips[0], ("09:00", "A"))
        self.assertEqual(saturday_trips[-1], ("20:30", "B"))


class TestHelpers(unittest.TestCase):

    def test_add_minutes(self):
        self.assertEqual(add_minutes("07:20", 6), "07:26")
        self.assertEqual(add_minutes("07:20", 8), "07:28")
        self.assertEqual(add_minutes("23:55", 10), "00:05")

    def test_get_stop_schedule_asr(self):
        schedule = get_stop_schedule(weekday_trips, "asr")
        self.assertEqual(len(schedule), 23)
        self.assertEqual(schedule[0], ("07:20", "A"))

    def test_get_stop_schedule_outram_exit_6(self):
        schedule = get_stop_schedule(weekday_trips, "outram_exit_6")
        self.assertEqual(schedule[0][0], "07:26")
        for time_str, _ in schedule:
            self.assertRegex(time_str, r'^\d{2}:\d{2}$')

    def test_get_stop_schedule_outram_exit_7(self):
        schedule = get_stop_schedule(weekday_trips, "outram_exit_7")
        self.assertEqual(schedule[0][0], "07:28")

    def test_get_stop_schedule_harbourfront(self):
        schedule = get_stop_schedule(weekday_trips, "harbourfront")
        b_count = sum(1 for _, t in weekday_trips if t == "B")
        self.assertEqual(len(schedule), b_count)

    def test_outram_stops_only_on_type_a(self):
        for trips in [weekday_trips, saturday_trips]:
            schedule = get_stop_schedule(trips, "outram_exit_6")
            for _, trip_type in schedule:
                self.assertEqual(trip_type, "A")

    def test_harbourfront_only_on_type_b(self):
        for trips in [weekday_trips, saturday_trips]:
            schedule = get_stop_schedule(trips, "harbourfront")
            for _, trip_type in schedule:
                self.assertEqual(trip_type, "B")

    def test_minutes_until(self):
        self.assertEqual(minutes_until(datetime.time(7, 0), datetime.time(7, 20)), 20)
        self.assertEqual(minutes_until(datetime.time(12, 30), datetime.time(13, 0)), 30)

    def test_stop_offsets(self):
        self.assertEqual(STOP_OFFSETS["asr"], 0)
        self.assertEqual(STOP_OFFSETS["outram_exit_6"], 6)
        self.assertEqual(STOP_OFFSETS["outram_exit_7"], 8)
        self.assertEqual(STOP_OFFSETS["harbourfront"], 10)

    def test_per_stop_chronological_order(self):
        for trips in [weekday_trips, saturday_trips]:
            for stop_key in STOP_OFFSETS:
                schedule = get_stop_schedule(trips, stop_key)
                prev = None
                for time_str, _ in schedule:
                    t = datetime.datetime.strptime(time_str, "%H:%M").time()
                    if prev:
                        self.assertGreater(t, prev, f"{stop_key} out of order at {time_str}")
                    prev = t


class TestDayType(unittest.TestCase):

    @patch('bus_bot.get_singapore_now')
    def test_weekday_detection(self, mock_now):
        for day in range(5):  # Mon-Fri
            mock_now.return_value = Mock(weekday=Mock(return_value=day))
            self.assertEqual(get_day_type(), "weekday")

    @patch('bus_bot.get_singapore_now')
    def test_saturday_detection(self, mock_now):
        mock_now.return_value = Mock(weekday=Mock(return_value=5))
        self.assertEqual(get_day_type(), "saturday")

    @patch('bus_bot.get_singapore_now')
    def test_sunday_detection(self, mock_now):
        mock_now.return_value = Mock(weekday=Mock(return_value=6))
        self.assertEqual(get_day_type(), "sunday")

    def test_get_trips_weekday(self):
        self.assertIs(get_trips_for_day_type("weekday"), weekday_trips)

    def test_get_trips_saturday(self):
        self.assertIs(get_trips_for_day_type("saturday"), saturday_trips)

    def test_get_trips_sunday(self):
        self.assertIsNone(get_trips_for_day_type("sunday"))


class TestNextBusTime(unittest.TestCase):

    def setUp(self):
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_update.message.reply_text = Mock()

    @patch('bus_bot.get_day_type', return_value="sunday")
    def test_sunday_no_service(self, _):
        self.mock_update.message.text = "ASR"
        next_bus_time(self.mock_update, self.mock_context)
        call_args = self.mock_update.message.reply_text.call_args[0][0]
        self.assertIn("no bus service on sundays", call_args.lower())

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_next_bus_asr_morning(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 25)))
        self.mock_update.message.text = "ASR"
        next_bus_time(self.mock_update, self.mock_context)
        calls = [c[0][0] for c in self.mock_update.message.reply_text.call_args_list]
        self.assertTrue(any("minutes" in c for c in calls))
        self.assertTrue(any("Heading to" in c for c in calls))

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_all_buses_passed(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(21, 0)))
        self.mock_update.message.text = "ASR"
        next_bus_time(self.mock_update, self.mock_context)
        calls = [c[0][0] for c in self.mock_update.message.reply_text.call_args_list]
        self.assertTrue(any("passed" in c.lower() for c in calls))

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_next_bus_harbourfront(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(10, 5)))
        self.mock_update.message.text = "Harbourfront MRT Exit D"
        next_bus_time(self.mock_update, self.mock_context)
        calls = [c[0][0] for c in self.mock_update.message.reply_text.call_args_list]
        self.assertTrue(any("minutes" in c for c in calls))

    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_invalid_location(self, _):
        self.mock_update.message.text = "somewhere else"
        next_bus_time(self.mock_update, self.mock_context)
        call_args = self.mock_update.message.reply_text.call_args[0][0]
        self.assertIn("Sorry", call_args)

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_case_insensitive(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        self.mock_update.message.text = "outram park mrt exit 6"
        next_bus_time(self.mock_update, self.mock_context)
        calls = [c[0][0] for c in self.mock_update.message.reply_text.call_args_list]
        self.assertTrue(any("minutes" in c for c in calls))


class TestGetSchedule(unittest.TestCase):

    def setUp(self):
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_update.message.reply_text = Mock()

    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_asr_schedule_display(self, _):
        self.mock_update.message.text = "ASR Schedule"
        get_schedule(self.mock_update, self.mock_context)
        self.assertEqual(self.mock_update.message.reply_text.call_count, 2)
        body = self.mock_update.message.reply_text.call_args_list[0][0][0]
        self.assertIn("07:20", body)
        self.assertIn("Outram Park MRT", body)
        self.assertIn("Harbourfront MRT Exit D", body)

    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_harbourfront_schedule_display(self, _):
        self.mock_update.message.text = "Harbourfront MRT Exit D Schedule"
        get_schedule(self.mock_update, self.mock_context)
        body = self.mock_update.message.reply_text.call_args_list[0][0][0]
        self.assertIn("Harbourfront MRT Exit D", body)
        self.assertNotIn("07:20", body)

    @patch('bus_bot.get_day_type', return_value="sunday")
    def test_sunday_shows_weekday(self, _):
        self.mock_update.message.text = "ASR Schedule"
        get_schedule(self.mock_update, self.mock_context)
        body = self.mock_update.message.reply_text.call_args_list[0][0][0]
        self.assertIn("Weekday", body)


class TestPromptLocation(unittest.TestCase):

    def setUp(self):
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_update.message.reply_text = Mock()

    @patch('bus_bot.get_day_type', return_value="sunday")
    def test_sunday_no_service(self, _):
        prompt_location(self.mock_update, self.mock_context)
        call_args = self.mock_update.message.reply_text.call_args[0][0]
        self.assertIn("no bus service on sundays", call_args.lower())


class TestFormatting(unittest.TestCase):

    def test_asr_schedule_contains_breaks(self):
        text = format_asr_schedule(weekday_trips, weekday_breaks, "20:15")
        self.assertIn("Driver Break", text)
        self.assertIn("Lunch Break", text)
        self.assertIn("Last drop-off: 20:15", text)

    def test_asr_schedule_contains_destinations(self):
        text = format_asr_schedule(weekday_trips, weekday_breaks, "20:15")
        self.assertIn("→ Outram Park MRT", text)
        self.assertIn("→ Harbourfront MRT Exit D", text)

    def test_stop_schedule_format(self):
        text = format_stop_schedule(weekday_trips, "outram_exit_6", weekday_breaks)
        self.assertIn("07:26", text)
        self.assertNotIn("→", text)


class TestButtonMaps(unittest.TestCase):

    def test_location_buttons_all_mapped(self):
        for button in LOCATION_BUTTONS:
            self.assertIn(button.lower(), LOCATION_BUTTON_MAP)

    def test_schedule_buttons_all_mapped(self):
        for button in SCHEDULE_BUTTONS:
            self.assertIn(button.lower(), SCHEDULE_BUTTON_MAP)


class TestScheduleAccuracy(unittest.TestCase):
    """Verify computed stop times match the official timetable screenshots."""

    @staticmethod
    def times(schedule):
        return [t for t, _ in schedule]

    def test_weekday_outram_exit_6_times(self):
        times = self.times(get_stop_schedule(weekday_trips, "outram_exit_6"))
        expected = [
            "07:26", "07:46", "08:06", "08:26", "09:06",
            "09:36", "10:36", "11:36",
            "13:36", "14:36",
            "16:36", "17:36", "18:36", "19:36",
        ]
        self.assertEqual(times, expected)

    def test_weekday_outram_exit_7_times(self):
        times = self.times(get_stop_schedule(weekday_trips, "outram_exit_7"))
        expected = [
            "07:28", "07:48", "08:08", "08:28", "09:08",
            "09:38", "10:38", "11:38",
            "13:38", "14:38",
            "16:38", "17:38", "18:38", "19:38",
        ]
        self.assertEqual(times, expected)

    def test_weekday_harbourfront_times(self):
        times = self.times(get_stop_schedule(weekday_trips, "harbourfront"))
        expected = [
            "10:10", "11:10",
            "13:10", "14:10", "15:10",
            "17:10", "18:10", "19:10", "20:10",
        ]
        self.assertEqual(times, expected)

    def test_saturday_outram_exit_6_times(self):
        times = self.times(get_stop_schedule(saturday_trips, "outram_exit_6"))
        expected = [
            "09:06", "10:06", "11:06", "12:06",
            "14:06", "15:06", "16:06",
            "18:06", "19:06", "20:06",
        ]
        self.assertEqual(times, expected)

    def test_saturday_outram_exit_7_times(self):
        times = self.times(get_stop_schedule(saturday_trips, "outram_exit_7"))
        expected = [
            "09:08", "10:08", "11:08", "12:08",
            "14:08", "15:08", "16:08",
            "18:08", "19:08", "20:08",
        ]
        self.assertEqual(times, expected)

    def test_saturday_harbourfront_times(self):
        times = self.times(get_stop_schedule(saturday_trips, "harbourfront"))
        expected = [
            "09:40", "10:40", "11:40", "12:40",
            "14:40", "15:40", "16:40",
            "18:40", "19:40", "20:40",
        ]
        self.assertEqual(times, expected)

    def test_saturday_asr_times(self):
        times = self.times(get_stop_schedule(saturday_trips, "asr"))
        expected = [
            "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
            "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
            "18:00", "18:30", "19:00", "19:30", "20:00", "20:30",
        ]
        self.assertEqual(times, expected)


class TestNextBusEdgeCases(unittest.TestCase):

    def setUp(self):
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_update.message.reply_text = Mock()

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_during_lunch_break_finds_next_trip(self, _, mock_now):
        """At 12:30 (weekday lunch break 12:00-13:00), next ASR bus is 13:00."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(12, 30)))
        self.mock_update.message.text = "ASR"
        next_bus_time(self.mock_update, self.mock_context)
        calls = [c[0][0] for c in self.mock_update.message.reply_text.call_args_list]
        first_reply = calls[0]
        self.assertIn("30 minutes", first_reply)
        self.assertIn("13:00", first_reply)

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_last_bus_no_following(self, _, mock_now):
        """At 19:55, next ASR bus is 20:00 (last one) — no following bus."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(19, 55)))
        self.mock_update.message.text = "ASR"
        next_bus_time(self.mock_update, self.mock_context)
        calls = [c[0][0] for c in self.mock_update.message.reply_text.call_args_list]
        self.assertTrue(any("5 minutes" in c for c in calls))
        self.assertTrue(any("no following bus" in c.lower() for c in calls))

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_next_bus_shows_following(self, _, mock_now):
        """At 07:00, next bus is 07:20 and following is 07:40 — both shown."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        self.mock_update.message.text = "ASR"
        next_bus_time(self.mock_update, self.mock_context)
        calls = [c[0][0] for c in self.mock_update.message.reply_text.call_args_list]
        self.assertTrue(any("07:20" in c for c in calls))
        self.assertTrue(any("07:40" in c for c in calls))

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="saturday")
    def test_saturday_next_bus(self, _, mock_now):
        """Saturday at 09:15, next ASR bus should be 09:30 (type B → Harbourfront)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(9, 15)))
        self.mock_update.message.text = "ASR"
        next_bus_time(self.mock_update, self.mock_context)
        calls = [c[0][0] for c in self.mock_update.message.reply_text.call_args_list]
        first_reply = calls[0]
        self.assertIn("15 minutes", first_reply)
        self.assertIn("Harbourfront", first_reply)

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="saturday")
    def test_saturday_all_buses_passed(self, _, mock_now):
        """Saturday at 21:00, all buses should have passed."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(21, 0)))
        self.mock_update.message.text = "Outram Park MRT Exit 6"
        next_bus_time(self.mock_update, self.mock_context)
        calls = [c[0][0] for c in self.mock_update.message.reply_text.call_args_list]
        self.assertTrue(any("passed" in c.lower() for c in calls))

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_harbourfront_during_morning_no_service(self, _, mock_now):
        """Weekday at 08:30, no Harbourfront buses yet (first is 10:10)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(8, 30)))
        self.mock_update.message.text = "Harbourfront MRT Exit D"
        next_bus_time(self.mock_update, self.mock_context)
        calls = [c[0][0] for c in self.mock_update.message.reply_text.call_args_list]
        first_reply = calls[0]
        self.assertIn("10:10", first_reply)

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_asr_destination_alternates(self, _, mock_now):
        """At 09:25, next ASR bus is 09:30 (A→Outram), following is 10:00 (B→Harbourfront)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(9, 25)))
        self.mock_update.message.text = "ASR"
        next_bus_time(self.mock_update, self.mock_context)
        calls = [c[0][0] for c in self.mock_update.message.reply_text.call_args_list]
        self.assertIn("Outram Park MRT", calls[0])
        self.assertIn("Harbourfront MRT Exit D", calls[1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
