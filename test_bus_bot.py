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


class TestBuildNextBusText(unittest.TestCase):

    @patch('bus_bot.get_singapore_now')
    def test_next_bus_asr_morning(self, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 25)))
        text = build_next_bus_text("asr", "weekday")
        self.assertIn("min", text)
        self.assertIn("Going to", text)

    @patch('bus_bot.get_singapore_now')
    def test_all_buses_passed(self, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(21, 0)))
        text = build_next_bus_text("asr", "weekday")
        self.assertIn("no more bus", text.lower())

    @patch('bus_bot.get_singapore_now')
    def test_next_bus_harbourfront(self, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(10, 5)))
        text = build_next_bus_text("harbourfront", "weekday")
        self.assertIn("min", text)


class TestLocationInlineKeyboard(unittest.TestCase):

    def setUp(self):
        self.mock_update = Mock()
        self.mock_context = Mock()

    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_prompt_location_sends_inline_keyboard(self, _):
        self.mock_update.message.reply_text = Mock()
        prompt_location(self.mock_update, self.mock_context)
        call_kwargs = self.mock_update.message.reply_text.call_args[1]
        reply_markup = call_kwargs.get("reply_markup")
        self.assertIsNotNone(reply_markup)
        buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
        self.assertEqual(len(buttons), len(STOP_NAMES))
        callback_data = [btn.callback_data for btn in buttons]
        for stop_key in STOP_NAMES:
            self.assertIn(f"location:{stop_key}", callback_data)

    @patch('bus_bot.get_day_type', return_value="sunday")
    def test_prompt_location_sunday_no_service(self, _):
        self.mock_update.message.reply_text = Mock()
        prompt_location(self.mock_update, self.mock_context)
        msg = self.mock_update.message.reply_text.call_args[0][0]
        self.assertIn("sunday no bus lah", msg.lower())

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_handle_location_callback_edits_message(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 25)))
        query = Mock()
        query.data = "location:asr"
        self.mock_update.callback_query = query
        handle_location_callback(self.mock_update, self.mock_context)
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        text = query.edit_message_text.call_args[0][0]
        self.assertIn("min", text)

    @patch('bus_bot.get_day_type', return_value="sunday")
    def test_handle_location_callback_sunday(self, _):
        query = Mock()
        query.data = "location:asr"
        self.mock_update.callback_query = query
        handle_location_callback(self.mock_update, self.mock_context)
        text = query.edit_message_text.call_args[0][0]
        self.assertIn("sunday no bus lah", text.lower())

    @patch('bus_bot.get_singapore_now')
    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_handle_location_callback_keeps_inline_keyboard(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        query = Mock()
        query.data = "location:outram_exit_6"
        self.mock_update.callback_query = query
        handle_location_callback(self.mock_update, self.mock_context)
        call_kwargs = query.edit_message_text.call_args[1]
        self.assertIn("reply_markup", call_kwargs)


class TestBuildScheduleText(unittest.TestCase):

    def test_asr_weekday_schedule(self):
        text = build_schedule_text("asr", "weekday")
        self.assertIn("07:20", text)
        self.assertIn("Outram Park MRT", text)
        self.assertIn("Harbourfront MRT Exit D", text)
        self.assertIn("Weekday", text)

    def test_harbourfront_weekday_schedule(self):
        text = build_schedule_text("harbourfront", "weekday")
        self.assertIn("Harbourfront MRT Exit D", text)
        self.assertNotIn("07:20", text)

    def test_saturday_schedule(self):
        text = build_schedule_text("asr", "saturday")
        self.assertIn("Saturday", text)
        self.assertIn("09:00", text)


class TestScheduleInlineKeyboard(unittest.TestCase):

    def setUp(self):
        self.mock_update = Mock()
        self.mock_context = Mock()

    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_prompt_schedule_sends_inline_keyboard(self, _):
        self.mock_update.message.reply_text = Mock()
        prompt_schedule(self.mock_update, self.mock_context)
        call_kwargs = self.mock_update.message.reply_text.call_args[1]
        reply_markup = call_kwargs.get("reply_markup")
        self.assertIsNotNone(reply_markup)
        buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
        self.assertEqual(len(buttons), len(STOP_NAMES))
        callback_data = [btn.callback_data for btn in buttons]
        for stop_key in STOP_NAMES:
            self.assertIn(f"schedule:{stop_key}", callback_data)

    @patch('bus_bot.get_day_type', return_value="sunday")
    def test_prompt_schedule_sunday_message(self, _):
        self.mock_update.message.reply_text = Mock()
        prompt_schedule(self.mock_update, self.mock_context)
        msg = self.mock_update.message.reply_text.call_args[0][0]
        self.assertIn("Sunday no bus lah", msg)

    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_handle_schedule_callback_edits_message(self, _):
        query = Mock()
        query.data = "schedule:asr"
        self.mock_update.callback_query = query
        handle_schedule_callback(self.mock_update, self.mock_context)
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        text = query.edit_message_text.call_args[0][0]
        self.assertIn("07:20", text)
        self.assertIn("Weekday", text)

    @patch('bus_bot.get_day_type', return_value="sunday")
    def test_handle_schedule_callback_sunday_shows_weekday(self, _):
        query = Mock()
        query.data = "schedule:asr"
        self.mock_update.callback_query = query
        handle_schedule_callback(self.mock_update, self.mock_context)
        text = query.edit_message_text.call_args[0][0]
        self.assertIn("Weekday", text)

    @patch('bus_bot.get_day_type', return_value="weekday")
    def test_handle_schedule_callback_keeps_inline_keyboard(self, _):
        query = Mock()
        query.data = "schedule:harbourfront"
        self.mock_update.callback_query = query
        handle_schedule_callback(self.mock_update, self.mock_context)
        call_kwargs = query.edit_message_text.call_args[1]
        self.assertIn("reply_markup", call_kwargs)


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

    @patch('bus_bot.get_singapore_now')
    def test_during_lunch_break_finds_next_trip(self, mock_now):
        """At 12:30 (weekday lunch break 12:00-13:00), next ASR bus is 13:00."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(12, 30)))
        text = build_next_bus_text("asr", "weekday")
        self.assertIn("30 min", text)
        self.assertIn("13:00", text)

    @patch('bus_bot.get_singapore_now')
    def test_last_bus_no_following(self, mock_now):
        """At 19:55, next ASR bus is 20:00 (last one) — no following bus."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(19, 55)))
        text = build_next_bus_text("asr", "weekday")
        self.assertIn("5 min", text)
        self.assertIn("last bus already", text.lower())

    @patch('bus_bot.get_singapore_now')
    def test_next_bus_shows_following(self, mock_now):
        """At 07:00, next bus is 07:20 and following is 07:40 — both shown."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        text = build_next_bus_text("asr", "weekday")
        self.assertIn("07:20", text)
        self.assertIn("07:40", text)

    @patch('bus_bot.get_singapore_now')
    def test_saturday_next_bus(self, mock_now):
        """Saturday at 09:15, next ASR bus should be 09:30 (type B → Harbourfront)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(9, 15)))
        text = build_next_bus_text("asr", "saturday")
        self.assertIn("15 min", text)
        self.assertIn("Harbourfront", text)

    @patch('bus_bot.get_singapore_now')
    def test_saturday_all_buses_passed(self, mock_now):
        """Saturday at 21:00, all buses should have passed."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(21, 0)))
        text = build_next_bus_text("outram_exit_6", "saturday")
        self.assertIn("no more bus", text.lower())

    @patch('bus_bot.get_singapore_now')
    def test_harbourfront_during_morning_no_service(self, mock_now):
        """Weekday at 08:30, no Harbourfront buses yet (first is 10:10)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(8, 30)))
        text = build_next_bus_text("harbourfront", "weekday")
        self.assertIn("10:10", text)

    @patch('bus_bot.get_singapore_now')
    def test_asr_destination_alternates(self, mock_now):
        """At 09:25, next ASR bus is 09:30 (A→Outram), following is 10:00 (B→Harbourfront)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(9, 25)))
        text = build_next_bus_text("asr", "weekday")
        self.assertIn("Outram Park MRT", text)
        self.assertIn("Harbourfront MRT Exit D", text)

    @patch('bus_bot.get_singapore_now')
    def test_exact_departure_time_still_shown(self, mock_now):
        """At exactly 07:20, the 07:20 bus should still be shown (0 min)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 20)))
        text = build_next_bus_text("asr", "weekday")
        self.assertIn("07:20", text)
        self.assertIn("0 min", text)

    @patch('bus_bot.get_singapore_now')
    def test_exact_last_bus_time(self, mock_now):
        """At exactly 20:00, the last bus should still be shown, not 'all passed'."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(20, 0)))
        text = build_next_bus_text("asr", "weekday")
        self.assertIn("20:00", text)
        self.assertNotIn("no more bus", text.lower())


class TestBotCommands(unittest.TestCase):

    @patch('bus_bot.Updater')
    def test_set_my_commands_called(self, mock_updater_class):
        from bus_bot import main
        mock_updater = mock_updater_class.return_value
        mock_bot = mock_updater.bot

        main()

        mock_bot.set_my_commands.assert_called_once()
        commands = mock_bot.set_my_commands.call_args[0][0]
        command_names = [c.command for c in commands]
        self.assertEqual(command_names, ["start", "location", "schedule"])


if __name__ == '__main__':
    unittest.main(verbosity=2)
