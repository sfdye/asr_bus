import datetime
from unittest.mock import AsyncMock, Mock, patch

from config import STOP_NAMES
from handlers.location import (
    build_next_bus_text,
    find_active_reminder,
    handle_cancel_callback,
    handle_location_callback,
    handle_remind_callback,
    location_inline_keyboard,
    prompt_location,
    send_reminder,
)


class TestBuildNextBusText:
    @patch("handlers.location.get_singapore_now")
    def test_next_bus_asr_morning(self, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 25)))
        text, _ = build_next_bus_text("asr", "weekday")
        assert "min" in text
        assert "Going to" in text

    @patch("handlers.location.get_singapore_now")
    def test_all_buses_passed(self, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(21, 0)))
        text, remind_info = build_next_bus_text("asr", "weekday")
        assert "no more bus" in text.lower()
        assert remind_info is None

    @patch("handlers.location.get_singapore_now")
    def test_next_bus_harbourfront(self, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(10, 5)))
        text, _ = build_next_bus_text("harbourfront", "weekday")
        assert "min" in text


class TestLocationInlineKeyboard:
    def setup_method(self):
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_context.job_queue.get_jobs_by_name.return_value = []

    @patch("handlers.location.get_day_type", return_value="weekday")
    async def test_prompt_location_sends_inline_keyboard(self, _):
        self.mock_update.message.reply_text = AsyncMock()
        await prompt_location(self.mock_update, self.mock_context)
        call_kwargs = self.mock_update.message.reply_text.call_args[1]
        reply_markup = call_kwargs.get("reply_markup")
        assert reply_markup is not None
        buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
        assert len(buttons) == len(STOP_NAMES)
        callback_data = [btn.callback_data for btn in buttons]
        for stop_key in STOP_NAMES:
            assert f"location:{stop_key}" in callback_data

    @patch("handlers.location.get_day_type", return_value="sunday")
    async def test_prompt_location_sunday_no_service(self, _):
        self.mock_update.message.reply_text = AsyncMock()
        await prompt_location(self.mock_update, self.mock_context)
        msg = self.mock_update.message.reply_text.call_args[0][0]
        assert "sunday no bus lah" in msg.lower()

    @patch("handlers.location.get_singapore_now")
    @patch("handlers.location.get_day_type", return_value="weekday")
    async def test_handle_location_callback_edits_message(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 25)))
        query = AsyncMock()
        query.data = "location:asr"
        self.mock_update.callback_query = query
        await handle_location_callback(self.mock_update, self.mock_context)
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        text = query.edit_message_text.call_args[0][0]
        assert "min" in text

    @patch("handlers.location.get_day_type", return_value="sunday")
    async def test_handle_location_callback_sunday(self, _):
        query = AsyncMock()
        query.data = "location:asr"
        self.mock_update.callback_query = query
        await handle_location_callback(self.mock_update, self.mock_context)
        text = query.edit_message_text.call_args[0][0]
        assert "sunday no bus lah" in text.lower()

    @patch("handlers.location.get_singapore_now")
    @patch("handlers.location.get_day_type", return_value="weekday")
    async def test_handle_location_callback_keeps_inline_keyboard(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        query = AsyncMock()
        query.data = "location:outram_exit_6"
        self.mock_update.callback_query = query
        await handle_location_callback(self.mock_update, self.mock_context)
        call_kwargs = query.edit_message_text.call_args[1]
        assert "reply_markup" in call_kwargs

    @patch("handlers.location.get_singapore_now")
    @patch("handlers.location.get_day_type", return_value="weekday")
    async def test_handle_location_callback_shows_active_reminder(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))

        def side_effect(name):
            return [Mock()] if name.endswith(":5") else []

        self.mock_context.job_queue.get_jobs_by_name.side_effect = side_effect
        query = AsyncMock()
        query.data = "location:asr"
        query.from_user.id = 12345
        self.mock_update.callback_query = query
        await handle_location_callback(self.mock_update, self.mock_context)
        reply_markup = query.edit_message_text.call_args[1]["reply_markup"]
        cancel_row = reply_markup.inline_keyboard[1]
        assert len(cancel_row) == 1
        assert "Reminder set" in cancel_row[0].text
        assert cancel_row[0].callback_data.startswith("cancel:")

    @patch("handlers.location.get_singapore_now")
    @patch("handlers.location.get_day_type", return_value="weekday")
    async def test_handle_location_callback_shows_remind_button_when_no_job(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        query = AsyncMock()
        query.data = "location:asr"
        query.from_user.id = 12345
        self.mock_update.callback_query = query
        await handle_location_callback(self.mock_update, self.mock_context)
        reply_markup = query.edit_message_text.call_args[1]["reply_markup"]
        remind_row = reply_markup.inline_keyboard[1]
        assert len(remind_row) == 1
        assert "Remind me" in remind_row[0].text
        assert remind_row[0].callback_data.startswith("remind:")


class TestNextBusEdgeCases:
    @patch("handlers.location.get_singapore_now")
    def test_during_lunch_break_finds_next_trip(self, mock_now):
        """At 12:30 (weekday lunch break 12:00-13:00), next ASR bus is 13:00."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(12, 30)))
        text, _ = build_next_bus_text("asr", "weekday")
        assert "30 min" in text
        assert "13:00" in text

    @patch("handlers.location.get_singapore_now")
    def test_last_bus_no_following(self, mock_now):
        """At 19:55, next ASR bus is 20:00 (last one) — no following bus."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(19, 55)))
        text, remind_info = build_next_bus_text("asr", "weekday")
        assert "5 min" in text
        assert "last bus already" in text.lower()
        assert remind_info["stop_key"] == "asr"
        assert remind_info["time_compact"] == "2000"
        assert remind_info["minutes_away"] == 5

    @patch("handlers.location.get_singapore_now")
    def test_next_bus_shows_following(self, mock_now):
        """At 07:00, next bus is 07:20 and following is 07:40 — both shown."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        text, _ = build_next_bus_text("asr", "weekday")
        assert "07:20" in text
        assert "07:40" in text

    @patch("handlers.location.get_singapore_now")
    def test_saturday_next_bus(self, mock_now):
        """Saturday at 09:15, next ASR bus should be 09:30 (type B → Harbourfront)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(9, 15)))
        text, _ = build_next_bus_text("asr", "saturday")
        assert "15 min" in text
        assert "Harbourfront" in text

    @patch("handlers.location.get_singapore_now")
    def test_saturday_all_buses_passed(self, mock_now):
        """Saturday at 21:00, all buses should have passed."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(21, 0)))
        text, remind_info = build_next_bus_text("outram_exit_6", "saturday")
        assert "no more bus" in text.lower()
        assert remind_info is None

    @patch("handlers.location.get_singapore_now")
    def test_harbourfront_during_morning_no_service(self, mock_now):
        """Weekday at 08:30, no Harbourfront buses yet (first is 10:10)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(8, 30)))
        text, _ = build_next_bus_text("harbourfront", "weekday")
        assert "10:10" in text

    @patch("handlers.location.get_singapore_now")
    def test_asr_destination_alternates(self, mock_now):
        """At 09:25, next ASR bus is 09:30 (A→Outram), following is 10:00 (B→Harbourfront)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(9, 25)))
        text, _ = build_next_bus_text("asr", "weekday")
        assert "Outram Park MRT" in text
        assert "Harbourfront MRT Exit D" in text

    @patch("handlers.location.get_singapore_now")
    def test_exact_departure_time_still_shown(self, mock_now):
        """At exactly 07:20, the 07:20 bus should still be shown (0 min)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 20)))
        text, _ = build_next_bus_text("asr", "weekday")
        assert "07:20" in text
        assert "0 min" in text

    @patch("handlers.location.get_singapore_now")
    def test_exact_last_bus_time(self, mock_now):
        """At exactly 20:00, the last bus should still be shown, not 'all passed'."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(20, 0)))
        text, _ = build_next_bus_text("asr", "weekday")
        assert "20:00" in text
        assert "no more bus" not in text.lower()


class TestFindActiveReminder:
    remind_info = {
        "stop_key": "asr",
        "time_compact": "0720",
        "trip_type": "A",
        "minutes_away": 20,
    }

    def test_returns_false_when_no_jobs(self):
        ctx = Mock()
        ctx.job_queue.get_jobs_by_name.return_value = []
        assert find_active_reminder(ctx, 12345, self.remind_info) is False

    def test_returns_true_when_job_exists(self):
        ctx = Mock()

        def side_effect(name):
            return [Mock()] if name.endswith(":5") else []

        ctx.job_queue.get_jobs_by_name.side_effect = side_effect
        assert find_active_reminder(ctx, 12345, self.remind_info) is True

    def test_returns_false_when_remind_info_is_none(self):
        ctx = Mock()
        assert find_active_reminder(ctx, 12345, None) is False


class TestRemindInfo:
    @patch("handlers.location.get_singapore_now")
    def test_remind_info_present_when_bus_far_enough(self, mock_now):
        """At 07:00, next bus at 07:20 is 20 min away — remind info should appear."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        _, remind_info = build_next_bus_text("asr", "weekday")
        assert remind_info == {
            "stop_key": "asr",
            "time_compact": "0720",
            "trip_type": "A",
            "minutes_away": 20,
        }

    @patch("handlers.location.get_singapore_now")
    def test_remind_info_none_when_bus_too_close(self, mock_now):
        """At 07:19, next bus at 07:20 is 1 min away — below MIN_REMIND_THRESHOLD."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 19)))
        _, remind_info = build_next_bus_text("asr", "weekday")
        assert remind_info is None

    @patch("handlers.location.get_singapore_now")
    def test_remind_info_present_at_threshold(self, mock_now):
        """At 07:18, next bus at 07:20 is 2 min away — equals MIN_REMIND_THRESHOLD."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 18)))
        _, remind_info = build_next_bus_text("asr", "weekday")
        assert remind_info is not None
        assert remind_info["minutes_away"] == 2

    @patch("handlers.location.get_singapore_now")
    def test_remind_info_none_when_no_buses(self, mock_now):
        """At 21:00, all buses passed — no remind info."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(21, 0)))
        _, remind_info = build_next_bus_text("asr", "weekday")
        assert remind_info is None

    @patch("handlers.location.get_singapore_now")
    def test_remind_info_for_non_asr_stop(self, mock_now):
        """At 07:00, next outram_exit_6 bus at 07:26."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        _, remind_info = build_next_bus_text("outram_exit_6", "weekday")
        assert remind_info["stop_key"] == "outram_exit_6"
        assert remind_info["time_compact"] == "0726"

    @patch("handlers.location.get_singapore_now")
    def test_remind_info_includes_trip_type(self, mock_now):
        """At 09:35, next harbourfront bus at 10:10 (type B)."""
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(9, 35)))
        _, remind_info = build_next_bus_text("harbourfront", "weekday")
        assert remind_info["trip_type"] == "B"
        assert remind_info["time_compact"] == "1010"


class TestLocationKeyboardRemindButton:
    remind_info = {
        "stop_key": "asr",
        "time_compact": "0720",
        "trip_type": "A",
        "minutes_away": 20,
    }

    def test_keyboard_without_remind_info(self):
        keyboard = location_inline_keyboard()
        assert len(keyboard.inline_keyboard) == len(STOP_NAMES)
        for row in keyboard.inline_keyboard:
            assert len(row) == 1
            assert row[0].callback_data.startswith("location:")

    def test_single_remind_button_shown_for_selected_stop(self):
        keyboard = location_inline_keyboard(remind_info=self.remind_info, selected_stop="asr")
        asr_stop_row = keyboard.inline_keyboard[0]
        assert asr_stop_row[0].callback_data == "location:asr"
        remind_row = keyboard.inline_keyboard[1]
        assert len(remind_row) == 1
        assert "Remind me" in remind_row[0].text
        assert remind_row[0].callback_data == "remind:asr:0720:A"

    def test_no_remind_button_without_selected_stop(self):
        keyboard = location_inline_keyboard(remind_info=self.remind_info)
        for row in keyboard.inline_keyboard:
            assert len(row) == 1
            assert row[0].callback_data.startswith("location:")

    def test_active_reminder_shows_cancel_button(self):
        keyboard = location_inline_keyboard(
            remind_info=self.remind_info, selected_stop="asr", active_reminder=True
        )
        cancel_row = keyboard.inline_keyboard[1]
        assert len(cancel_row) == 1
        assert cancel_row[0].callback_data == "cancel:asr:0720:A"
        assert "Reminder set" in cancel_row[0].text

    def test_active_reminder_hides_remind_button(self):
        keyboard = location_inline_keyboard(
            remind_info=self.remind_info, selected_stop="asr", active_reminder=True
        )
        for row in keyboard.inline_keyboard:
            for btn in row:
                assert "Remind me" not in btn.text


class TestHandleRemindCallback:
    def setup_method(self):
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_context.job_queue = Mock()

    @patch("handlers.location.get_singapore_now")
    @patch("handlers.location.get_day_type", return_value="weekday")
    async def test_remind_schedules_multiple_jobs_for_far_bus(self, _, mock_now):
        """Bus 20 min away should schedule 2 reminders (5 min + 2 min before)."""
        mock_now.return_value = datetime.datetime(2026, 1, 5, 7, 0, tzinfo=datetime.UTC)
        query = AsyncMock()
        query.data = "remind:asr:0720:A"
        query.from_user.id = 12345
        query.message.chat_id = 67890
        self.mock_update.callback_query = query
        self.mock_context.job_queue.get_jobs_by_name.return_value = []

        await handle_remind_callback(self.mock_update, self.mock_context)

        query.answer.assert_called_once()
        assert self.mock_context.job_queue.run_once.call_count == 2
        calls = self.mock_context.job_queue.run_once.call_args_list
        lead_times = sorted(c[1]["data"]["lead_minutes"] for c in calls)
        assert lead_times == [2, 5]

    @patch("handlers.location.get_singapore_now")
    @patch("handlers.location.get_day_type", return_value="weekday")
    async def test_remind_schedules_single_job_for_medium_bus(self, _, mock_now):
        """Bus 7 min away should schedule 1 reminder (3 min before)."""
        mock_now.return_value = datetime.datetime(2026, 1, 5, 7, 13, tzinfo=datetime.UTC)
        query = AsyncMock()
        query.data = "remind:asr:0720:A"
        query.from_user.id = 12345
        query.message.chat_id = 67890
        self.mock_update.callback_query = query
        self.mock_context.job_queue.get_jobs_by_name.return_value = []

        await handle_remind_callback(self.mock_update, self.mock_context)

        assert self.mock_context.job_queue.run_once.call_count == 1
        call_kwargs = self.mock_context.job_queue.run_once.call_args[1]
        assert call_kwargs["data"]["lead_minutes"] == 3

    @patch("handlers.location.get_singapore_now")
    @patch("handlers.location.get_day_type", return_value="weekday")
    async def test_remind_schedules_immediate_for_close_bus(self, _, mock_now):
        """Bus 3 min away should schedule immediate reminder (0 min lead)."""
        mock_now.return_value = datetime.datetime(2026, 1, 5, 7, 17, tzinfo=datetime.UTC)
        query = AsyncMock()
        query.data = "remind:asr:0720:A"
        query.from_user.id = 12345
        query.message.chat_id = 67890
        self.mock_update.callback_query = query
        self.mock_context.job_queue.get_jobs_by_name.return_value = []

        await handle_remind_callback(self.mock_update, self.mock_context)

        assert self.mock_context.job_queue.run_once.call_count == 1
        call_kwargs = self.mock_context.job_queue.run_once.call_args[1]
        assert call_kwargs["data"]["lead_minutes"] == 0

    @patch("handlers.location.get_singapore_now")
    async def test_remind_rejects_stale_bus(self, mock_now):
        mock_now.return_value = datetime.datetime(2026, 1, 5, 8, 0, tzinfo=datetime.UTC)
        query = AsyncMock()
        query.data = "remind:asr:0720:A"
        query.from_user.id = 12345
        query.message.chat_id = 67890
        self.mock_update.callback_query = query

        await handle_remind_callback(self.mock_update, self.mock_context)

        text = query.edit_message_text.call_args[0][0]
        assert "already gone" in text.lower()

    @patch("handlers.location.get_singapore_now")
    @patch("handlers.location.get_day_type", return_value="weekday")
    async def test_remind_dedup_existing_jobs(self, _, mock_now):
        """Existing jobs should not be re-created."""
        mock_now.return_value = datetime.datetime(2026, 1, 5, 7, 0, tzinfo=datetime.UTC)
        query = AsyncMock()
        query.data = "remind:asr:0720:A"
        query.from_user.id = 12345
        query.message.chat_id = 67890
        self.mock_update.callback_query = query
        self.mock_context.job_queue.get_jobs_by_name.return_value = [Mock()]

        await handle_remind_callback(self.mock_update, self.mock_context)

        self.mock_context.job_queue.run_once.assert_not_called()

    @patch("handlers.location.get_singapore_now")
    @patch("handlers.location.get_day_type", return_value="weekday")
    async def test_remind_shows_cancel_button(self, _, mock_now):
        mock_now.return_value = datetime.datetime(2026, 1, 5, 7, 0, tzinfo=datetime.UTC)
        query = AsyncMock()
        query.data = "remind:asr:0720:A"
        query.from_user.id = 12345
        query.message.chat_id = 67890
        self.mock_update.callback_query = query
        self.mock_context.job_queue.get_jobs_by_name.return_value = []

        await handle_remind_callback(self.mock_update, self.mock_context)

        reply_markup = query.edit_message_text.call_args[1]["reply_markup"]
        cancel_row = reply_markup.inline_keyboard[1]
        assert len(cancel_row) == 1
        assert "Reminder set" in cancel_row[0].text

    async def test_remind_rejects_invalid_data(self):
        query = AsyncMock()
        query.data = "remind:bad"
        self.mock_update.callback_query = query

        await handle_remind_callback(self.mock_update, self.mock_context)
        query.edit_message_text.assert_not_called()


class TestSendReminder:
    async def test_early_reminder_tone(self):
        """5 min lead → 'time to get ready' tone."""
        mock_context = Mock()
        mock_context.bot.send_message = AsyncMock()
        mock_context.job.data = {
            "chat_id": 67890,
            "stop_key": "asr",
            "departure_time": "08:00",
            "trip_type": "A",
            "lead_minutes": 5,
        }

        await send_reminder(mock_context)

        text = mock_context.bot.send_message.call_args[1]["text"]
        assert "5 min" in text
        assert "get ready" in text.lower()
        assert "Outram Park MRT" in text

    async def test_urgent_reminder_tone(self):
        """2 min lead → 'go go go' tone."""
        mock_context = Mock()
        mock_context.bot.send_message = AsyncMock()
        mock_context.job.data = {
            "chat_id": 67890,
            "stop_key": "asr",
            "departure_time": "08:00",
            "trip_type": "A",
            "lead_minutes": 2,
        }

        await send_reminder(mock_context)

        text = mock_context.bot.send_message.call_args[1]["text"]
        assert "2 min" in text
        assert "go go go" in text.lower()

    async def test_immediate_reminder_tone(self):
        """0 min lead → 'queue for boarding' tone."""
        mock_context = Mock()
        mock_context.bot.send_message = AsyncMock()
        mock_context.job.data = {
            "chat_id": 67890,
            "stop_key": "harbourfront",
            "departure_time": "10:10",
            "trip_type": "B",
            "lead_minutes": 0,
        }

        await send_reminder(mock_context)

        text = mock_context.bot.send_message.call_args[1]["text"]
        assert "boarding" in text.lower()
        assert "Avenue South Residence" in text

    async def test_non_asr_stop_shows_asr_destination(self):
        mock_context = Mock()
        mock_context.bot.send_message = AsyncMock()
        mock_context.job.data = {
            "chat_id": 67890,
            "stop_key": "harbourfront",
            "departure_time": "10:10",
            "trip_type": "B",
            "lead_minutes": 3,
        }

        await send_reminder(mock_context)

        text = mock_context.bot.send_message.call_args[1]["text"]
        assert "Avenue South Residence" in text


class TestHandleCancelCallback:
    def setup_method(self):
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_context.job_queue = Mock()

    @patch("handlers.location.get_singapore_now")
    @patch("handlers.location.get_day_type", return_value="weekday")
    async def test_cancel_removes_all_jobs(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        mock_jobs = {":5": [Mock()], ":2": [Mock()]}

        def side_effect(name):
            for suffix, jobs in mock_jobs.items():
                if name.endswith(suffix):
                    return jobs
            return []

        self.mock_context.job_queue.get_jobs_by_name.side_effect = side_effect
        query = AsyncMock()
        query.data = "cancel:asr:0720:A"
        query.from_user.id = 12345
        self.mock_update.callback_query = query

        await handle_cancel_callback(self.mock_update, self.mock_context)

        for jobs in mock_jobs.values():
            for job in jobs:
                job.schedule_removal.assert_called_once()

    @patch("handlers.location.get_singapore_now")
    @patch("handlers.location.get_day_type", return_value="weekday")
    async def test_cancel_shows_remind_button_again(self, _, mock_now):
        mock_now.return_value = Mock(time=Mock(return_value=datetime.time(7, 0)))
        self.mock_context.job_queue.get_jobs_by_name.return_value = []
        query = AsyncMock()
        query.data = "cancel:asr:0720:A"
        query.from_user.id = 12345
        self.mock_update.callback_query = query

        await handle_cancel_callback(self.mock_update, self.mock_context)

        query.answer.assert_called_once()
        reply_markup = query.edit_message_text.call_args[1]["reply_markup"]
        remind_row = reply_markup.inline_keyboard[1]
        assert len(remind_row) == 1
        assert "Remind me" in remind_row[0].text

    async def test_cancel_rejects_invalid_data(self):
        query = AsyncMock()
        query.data = "cancel:bad"
        self.mock_update.callback_query = query

        await handle_cancel_callback(self.mock_update, self.mock_context)
        query.edit_message_text.assert_not_called()
