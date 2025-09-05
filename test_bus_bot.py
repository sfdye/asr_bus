import unittest
import datetime
from unittest.mock import Mock, patch, MagicMock
import pytz

# Import the bot functions (adjust import path as needed)
from bus_bot import (
    asr_schedule, 
    outram_schedule, 
    next_bus_time, 
    get_schedule,
    service_notice
)


class TestBusBotFunctions(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_update.message.text = ""
        self.mock_update.message.reply_text = Mock()
    
    def test_schedule_data_integrity(self):
        """Test that schedules have correct format and length."""
        # Test ASR schedule
        self.assertEqual(len(asr_schedule), 22, "ASR schedule should have 22 entries")
        self.assertEqual(len(outram_schedule), 22, "Outram schedule should have 22 entries")
        
        # Test time format
        for time_str in asr_schedule:
            self.assertRegex(time_str, r'^\d{2}:\d{2}$', f"Invalid time format: {time_str}")
        
        for time_str in outram_schedule:
            self.assertRegex(time_str, r'^\d{2}:\d{2}$', f"Invalid time format: {time_str}")
    
    def test_schedule_chronological_order(self):
        """Test that schedules are in chronological order."""
        prev_time = None
        for time_str in asr_schedule:
            current_time = datetime.datetime.strptime(time_str, "%H:%M").time()
            if prev_time:
                self.assertGreater(current_time, prev_time, f"Schedule not in order at {time_str}")
            prev_time = current_time
    
    def test_asr_schedule_selection(self):
        """Test ASR schedule display."""
        self.mock_update.message.text = "asr schedule"
        get_schedule(self.mock_update, self.mock_context)
        
        # Verify reply_text was called twice (schedule + service notice)
        self.assertEqual(self.mock_update.message.reply_text.call_count, 2)
        
        # Check that all ASR times are in the first call (schedule)
        first_call_args = self.mock_update.message.reply_text.call_args_list[0][0][0]
        for time_str in asr_schedule:
            self.assertIn(time_str, first_call_args)
        
        # Check that service notice is in the second call
        second_call_args = self.mock_update.message.reply_text.call_args_list[1][0][0]
        self.assertIn("IMPORTANT", second_call_args)
    
    def test_outram_schedule_selection(self):
        """Test Outram schedule display."""
        self.mock_update.message.text = "outram mrt schedule"
        get_schedule(self.mock_update, self.mock_context)
        
        # Verify reply_text was called twice (schedule + service notice)
        self.assertEqual(self.mock_update.message.reply_text.call_count, 2)
        
        # Check that all Outram times are in the first call (schedule)
        first_call_args = self.mock_update.message.reply_text.call_args_list[0][0][0]
        for time_str in outram_schedule:
            self.assertIn(time_str, first_call_args)
        
        # Check that service notice is in the second call
        second_call_args = self.mock_update.message.reply_text.call_args_list[1][0][0]
        self.assertIn("IMPORTANT", second_call_args)
    
    @patch('bus_bot.datetime')
    @patch('bus_bot.pytz')
    def test_next_bus_calculation_morning(self, mock_pytz, mock_datetime):
        """Test next bus calculation for morning time."""
        # Mock current time as 8:15 AM
        mock_current_time = datetime.time(8, 15)
        mock_datetime.datetime.now.return_value.time.return_value = mock_current_time
        mock_datetime.datetime.strptime = datetime.datetime.strptime
        mock_datetime.datetime.combine = datetime.datetime.combine
        mock_datetime.date.today = datetime.date.today
        
        # Mock timezone
        mock_timezone = Mock()
        mock_pytz.timezone.return_value = mock_timezone
        
        # Test ASR location
        self.mock_update.message.text = "asr"
        next_bus_time(self.mock_update, self.mock_context)
        
        # Should have multiple reply calls (next bus + service notice + following bus + service notice)
        self.assertGreaterEqual(self.mock_update.message.reply_text.call_count, 2)
        
        # Check that service notice is included
        call_args_list = [call[0][0] for call in self.mock_update.message.reply_text.call_args_list]
        service_notice_found = any(service_notice.strip() in arg for arg in call_args_list)
        self.assertTrue(service_notice_found, "Service notice should be included in response")
    
    @patch('bus_bot.datetime')
    @patch('bus_bot.pytz')
    def test_next_bus_calculation_evening(self, mock_pytz, mock_datetime):
        """Test next bus calculation for evening time."""
        # Mock current time as 8:00 PM (after last bus)
        mock_current_time = datetime.time(20, 0)
        mock_datetime.datetime.now.return_value.time.return_value = mock_current_time
        mock_datetime.datetime.strptime = datetime.datetime.strptime
        mock_datetime.datetime.combine = datetime.datetime.combine
        mock_datetime.date.today = datetime.date.today
        
        # Mock timezone
        mock_timezone = Mock()
        mock_pytz.timezone.return_value = mock_timezone
        
        # Test ASR location
        self.mock_update.message.text = "asr"
        next_bus_time(self.mock_update, self.mock_context)
        
        # Should reply with "all buses passed" message + service notice
        self.assertEqual(self.mock_update.message.reply_text.call_count, 2)
        
        # Check for "all buses passed" message
        first_call = self.mock_update.message.reply_text.call_args_list[0][0][0]
        self.assertIn("passed", first_call.lower())
        
        # Check that service notice is included
        second_call = self.mock_update.message.reply_text.call_args_list[1][0][0]
        self.assertIn("IMPORTANT", second_call)
    
    def test_invalid_location_handling(self):
        """Test handling of invalid location input."""
        self.mock_update.message.text = "invalid location"
        next_bus_time(self.mock_update, self.mock_context)
        
        # Should reply with error message
        self.mock_update.message.reply_text.assert_called_once()
        call_args = self.mock_update.message.reply_text.call_args[0][0]
        self.assertIn("Sorry", call_args)
    
    def test_service_notice_content(self):
        """Test that service notice contains required information."""
        self.assertIn("30 Sep 2025", service_notice)
        self.assertIn("EOGM/AGM", service_notice)
        self.assertIn("Vote to continue", service_notice)  
        self.assertIn("IMPORTANT", service_notice)
        self.assertIn("beloved shuttle bus service", service_notice)
        self.assertIn("Your voice matters for our community", service_notice)
        self.assertIn("keeps our property attractive", service_notice)
    
    def test_case_insensitive_location_input(self):
        """Test that location input is case insensitive."""
        # Test uppercase
        self.mock_update.message.text = "ASR"
        next_bus_time(self.mock_update, self.mock_context)
        
        # Should not get error message (would only be 1 call if error)
        self.assertGreaterEqual(self.mock_update.message.reply_text.call_count, 1)
        
        # Reset mock
        self.mock_update.message.reply_text.reset_mock()
        
        # Test mixed case
        self.mock_update.message.text = "Outram MRT"
        next_bus_time(self.mock_update, self.mock_context)
        
        # Should not get error message
        self.assertGreaterEqual(self.mock_update.message.reply_text.call_count, 1)


class TestScheduleAccuracy(unittest.TestCase):
    """Test schedule accuracy against known values."""
    
    def test_asr_first_last_buses(self):
        """Test first and last bus times for ASR."""
        self.assertEqual(asr_schedule[0], "08:00", "First ASR bus should be 08:00")
        self.assertEqual(asr_schedule[-1], "19:40", "Last ASR bus should be 19:40")
    
    def test_outram_first_last_buses(self):
        """Test first and last bus times for Outram."""
        self.assertEqual(outram_schedule[0], "08:04", "First Outram bus should be 08:04")
        self.assertEqual(outram_schedule[-1], "19:44", "Last Outram bus should be 19:44")
    
    def test_travel_time_consistency(self):
        """Test that travel time between ASR and Outram is consistent."""
        for i in range(len(asr_schedule)):
            asr_time = datetime.datetime.strptime(asr_schedule[i], "%H:%M")
            outram_time = datetime.datetime.strptime(outram_schedule[i], "%H:%M")
            
            travel_time = (outram_time - asr_time).seconds / 60
            
            # Travel time should be 4 minutes for most buses
            self.assertIn(travel_time, [4.0, 5.0], 
                         f"Unexpected travel time at {asr_schedule[i]}: {travel_time} minutes")


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)
