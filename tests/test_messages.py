"""
Unit tests for MessageFormatter
"""

import unittest
from datetime import datetime

from ui.messages import MessageFormatter
from models.user_session import UserSession
from models.ping import PingRecord
from config.constants import ConversationState


class TestMessageFormatter(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 12345
        self.username = "testuser"
        self.session = UserSession(user_id=self.user_id, username=self.username)
        
        self.ping = PingRecord(
            organizer_id=67890,
            organizer_name="alice",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["testuser", "bob", "charlie"]
        )
    
    def test_format_welcome_message_with_username(self):
        """Test welcome message formatting with username"""
        message = MessageFormatter.format_welcome_message("Alice")
        
        self.assertIn("Welcome to UniLinkUp, Alice!", message)
        self.assertIn("/lunch", message)
        self.assertIn("/study", message)
        self.assertIn("/recent", message)
    
    def test_format_welcome_message_without_username(self):
        """Test welcome message formatting without username"""
        message = MessageFormatter.format_welcome_message()
        
        self.assertIn("Welcome to UniLinkUp!", message)
        self.assertNotIn("Welcome to UniLinkUp,", message)  # No comma for generic welcome
        self.assertIn("/lunch", message)
        self.assertIn("/study", message)
    
    def test_format_meetup_prompt(self):
        """Test meetup prompt formatting"""
        lunch_prompt = MessageFormatter.format_meetup_prompt("lunch")
        self.assertIn("lunch", lunch_prompt.lower())
        self.assertIn("🍽️", lunch_prompt)
        
        study_prompt = MessageFormatter.format_meetup_prompt("study")
        self.assertIn("study", study_prompt.lower())
        self.assertIn("📚", study_prompt)
        
        # Test unknown meetup type
        custom_prompt = MessageFormatter.format_meetup_prompt("coffee")
        self.assertIn("coffee", custom_prompt)
        self.assertIn("Where would you like to meet", custom_prompt)
    
    def test_format_time_prompt(self):
        """Test time prompt formatting"""
        prompt = MessageFormatter.format_time_prompt()
        
        self.assertIn("⏰", prompt)
        self.assertIn("When would you like to meet", prompt)
        self.assertIn("/skip", prompt)
    
    def test_format_friends_prompt(self):
        """Test friends prompt formatting"""
        # No friends selected
        prompt = MessageFormatter.format_friends_prompt(0)
        self.assertIn("👥", prompt)
        self.assertIn("Who would you like to invite", prompt)
        self.assertNotIn("Currently selected", prompt)
        
        # Some friends selected
        prompt = MessageFormatter.format_friends_prompt(2)
        self.assertIn("Currently selected: 2 friends", prompt)
        
        # One friend selected
        prompt = MessageFormatter.format_friends_prompt(1)
        self.assertIn("Currently selected: 1 friend", prompt)
        self.assertNotIn("friends", prompt.split("1 friend")[1])  # Should be singular
    
    def test_format_confirmation_message(self):
        """Test confirmation message formatting"""
        # Set up session with complete data
        self.session.set_meetup_type("lunch")
        self.session.set_location("Campus Café")
        self.session.set_time("12:30 PM")
        self.session.toggle_friend("Alice")
        self.session.toggle_friend("Bob")
        
        message = MessageFormatter.format_confirmation_message(self.session)
        
        self.assertIn("✅", message)
        self.assertIn("Campus Café", message)
        self.assertIn("12:30 PM", message)
        self.assertIn("Alice", message)
        self.assertIn("Bob", message)
    
    def test_format_confirmation_message_minimal(self):
        """Test confirmation message with minimal data"""
        self.session.set_meetup_type("study")
        # No location, time, or friends set
        
        message = MessageFormatter.format_confirmation_message(self.session)
        
        self.assertIn("Not specified", message)  # Location
        self.assertIn("Flexible time", message)  # Time
        self.assertIn("None selected", message)  # Friends
    
    def test_format_invitation_notification(self):
        """Test invitation notification formatting"""
        message = MessageFormatter.format_invitation_notification(self.ping, "testuser")
        
        self.assertIn("🔔", message)
        self.assertIn("lunch", message)
        self.assertIn("alice", message)
        self.assertIn("Campus Café", message)
        self.assertIn("12:30 PM", message)
        self.assertIn("bob", message)
        self.assertIn("charlie", message)
        self.assertNotIn("testuser", message.split("from alice")[1])  # Recipient excluded from "also invited"
    
    def test_format_invitation_notification_flexible_time(self):
        """Test invitation notification with flexible time"""
        ping_no_time = PingRecord(
            organizer_id=67890,
            organizer_name="alice",
            meetup_type="study",
            location="Library",
            time="",  # No specific time
            invited_friends=["testuser", "bob"]
        )
        
        message = MessageFormatter.format_invitation_notification(ping_no_time, "testuser")
        
        self.assertIn("Flexible time", message)
        self.assertIn("study", message)
    
    def test_format_recent_pings_empty(self):
        """Test recent pings formatting with no pings"""
        message = MessageFormatter.format_recent_pings([])
        
        self.assertIn("📭", message)
        self.assertIn("No recent invitations", message)
    
    def test_format_recent_pings_with_data(self):
        """Test recent pings formatting with data"""
        ping1 = PingRecord(
            organizer_id=11111,
            organizer_name="alice",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["bob"]
        )
        
        ping2 = PingRecord(
            organizer_id=22222,
            organizer_name="bob",
            meetup_type="study",
            location="Library",
            time="2:00 PM",
            invited_friends=["alice", "charlie"]
        )
        
        pings = [ping1, ping2]
        message = MessageFormatter.format_recent_pings(pings)
        
        self.assertIn("📋", message)
        self.assertIn("Recent Invitations", message)
        self.assertIn("1.", message)
        self.assertIn("2.", message)
        self.assertIn("alice", message)
        self.assertIn("bob", message)
        self.assertIn("Campus Café", message)
        self.assertIn("Library", message)
    
    def test_format_invitation_sent_message(self):
        """Test invitation sent message formatting"""
        # Single friend
        message = MessageFormatter.format_invitation_sent_message(1)
        self.assertIn("🎉", message)
        self.assertIn("friend has been", message)  # Singular
        
        # Multiple friends
        message = MessageFormatter.format_invitation_sent_message(3)
        self.assertIn("🎉", message)
        self.assertIn("3 friends have been", message)  # Plural
    
    def test_format_error_message(self):
        """Test error message formatting"""
        # Known error types
        invalid_time = MessageFormatter.format_error_message("invalid_time")
        self.assertIn("⚠️", invalid_time)
        self.assertIn("Invalid time", invalid_time)
        
        no_friends = MessageFormatter.format_error_message("no_friends")
        self.assertIn("select at least one friend", no_friends)
        
        general = MessageFormatter.format_error_message("general")
        self.assertIn("Something went wrong", general)
        
        timeout = MessageFormatter.format_error_message("timeout")
        self.assertIn("timed out", timeout)
        
        # Unknown error type
        unknown = MessageFormatter.format_error_message("unknown_type")
        self.assertIn("Something went wrong", unknown)  # Should default to general
        
        # Custom message
        custom = MessageFormatter.format_error_message("any_type", "Custom error message")
        self.assertEqual(custom, "⚠️ Custom error message")
    
    def test_format_session_summary(self):
        """Test session summary formatting"""
        self.session.set_meetup_type("lunch")
        self.session.set_location("Campus Café")
        self.session.current_state = ConversationState.FRIENDS
        self.session.toggle_friend("Alice")
        
        summary = MessageFormatter.format_session_summary(self.session)
        
        self.assertIn("👤", summary)
        self.assertIn("testuser", summary)
        self.assertIn(str(self.user_id), summary)
        self.assertIn("lunch", summary)
        self.assertIn("Campus Café", summary)
        self.assertIn("Alice", summary)
        self.assertIn("friends", summary)
    
    def test_format_ping_summary(self):
        """Test ping summary formatting"""
        summary = MessageFormatter.format_ping_summary(self.ping)
        
        # Should use the ping's format_for_display method
        expected = self.ping.format_for_display()
        self.assertEqual(summary, expected)
    
    def test_format_help_message(self):
        """Test help message formatting"""
        help_msg = MessageFormatter.format_help_message()
        
        self.assertIn("🆘", help_msg)
        self.assertIn("UniLinkUp Help", help_msg)
        self.assertIn("/lunch", help_msg)
        self.assertIn("/study", help_msg)
        self.assertIn("/recent", help_msg)
        self.assertIn("/help", help_msg)
        self.assertIn("How it works", help_msg)
        self.assertIn("Tips", help_msg)
    
    def test_format_cancel_message(self):
        """Test cancel message formatting"""
        message = MessageFormatter.format_cancel_message()
        
        self.assertIn("❌", message)
        self.assertIn("cancelled", message)
        self.assertIn("/lunch", message)
        self.assertIn("/study", message)
    
    def test_format_time_display(self):
        """Test time display formatting"""
        # Normal time
        self.assertEqual(MessageFormatter.format_time_display("2:30 PM"), "2:30 PM")
        
        # Empty time
        self.assertEqual(MessageFormatter.format_time_display(""), "Flexible time")
        self.assertEqual(MessageFormatter.format_time_display(None), "Flexible time")
        
        # Whitespace time
        self.assertEqual(MessageFormatter.format_time_display("   "), "Flexible time")
        
        # Time with whitespace
        self.assertEqual(MessageFormatter.format_time_display("  2:30 PM  "), "2:30 PM")
    
    def test_format_location_selected_message(self):
        """Test location selected message formatting"""
        message = MessageFormatter.format_location_selected_message("Campus Café")
        
        self.assertIn("📍", message)
        self.assertIn("Great choice", message)
        self.assertIn("Campus Café", message)
        self.assertIn("When would you like to meet", message)  # Should include time prompt
    
    def test_format_time_set_message(self):
        """Test time set message formatting"""
        message = MessageFormatter.format_time_set_message("2:30 PM")
        
        self.assertIn("⏰", message)
        self.assertIn("Time set", message)
        self.assertIn("2:30 PM", message)
        self.assertIn("Who would you like to invite", message)  # Should include friends prompt
    
    def test_format_friends_updated_message(self):
        """Test friends updated message formatting"""
        # No friends selected
        message = MessageFormatter.format_friends_updated_message(self.session)
        self.assertIn("👥", message)
        self.assertIn("No friends selected", message)
        
        # Some friends selected
        self.session.toggle_friend("Alice")
        self.session.toggle_friend("Bob")
        
        message = MessageFormatter.format_friends_updated_message(self.session)
        self.assertIn("Selected friends", message)
        self.assertIn("Alice", message)
        self.assertIn("Bob", message)
        self.assertIn("Select more friends or confirm", message)


if __name__ == "__main__":
    unittest.main()