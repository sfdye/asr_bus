from unittest.mock import AsyncMock, Mock, patch

from config import STOP_NAMES
from handlers.schedule import (
    build_schedule_text,
    handle_schedule_callback,
    prompt_schedule,
)


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

    @patch("handlers.schedule.get_day_type", return_value="weekday")
    async def test_prompt_schedule_sends_inline_keyboard(self, _):
        self.mock_update.message.reply_text = AsyncMock()
        await prompt_schedule(self.mock_update, self.mock_context)
        call_kwargs = self.mock_update.message.reply_text.call_args[1]
        reply_markup = call_kwargs.get("reply_markup")
        assert reply_markup is not None
        buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
        assert len(buttons) == len(STOP_NAMES)
        callback_data = [btn.callback_data for btn in buttons]
        for stop_key in STOP_NAMES:
            assert f"schedule:{stop_key}" in callback_data

    @patch("handlers.schedule.get_day_type", return_value="sunday")
    async def test_prompt_schedule_sunday_message(self, _):
        self.mock_update.message.reply_text = AsyncMock()
        await prompt_schedule(self.mock_update, self.mock_context)
        msg = self.mock_update.message.reply_text.call_args[0][0]
        assert "Sunday no bus lah" in msg

    @patch("handlers.schedule.get_day_type", return_value="weekday")
    async def test_handle_schedule_callback_edits_message(self, _):
        query = AsyncMock()
        query.data = "schedule:asr"
        self.mock_update.callback_query = query
        await handle_schedule_callback(self.mock_update, self.mock_context)
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        text = query.edit_message_text.call_args[0][0]
        assert "07:20" in text
        assert "Weekday" in text

    @patch("handlers.schedule.get_day_type", return_value="sunday")
    async def test_handle_schedule_callback_sunday_shows_weekday(self, _):
        query = AsyncMock()
        query.data = "schedule:asr"
        self.mock_update.callback_query = query
        await handle_schedule_callback(self.mock_update, self.mock_context)
        text = query.edit_message_text.call_args[0][0]
        assert "Weekday" in text

    @patch("handlers.schedule.get_day_type", return_value="weekday")
    async def test_handle_schedule_callback_keeps_inline_keyboard(self, _):
        query = AsyncMock()
        query.data = "schedule:harbourfront"
        self.mock_update.callback_query = query
        await handle_schedule_callback(self.mock_update, self.mock_context)
        call_kwargs = query.edit_message_text.call_args[1]
        assert "reply_markup" in call_kwargs
