"""
Unit tests for UserSession model
"""

import unittest
from datetime import datetime, timedelta
from models.user_session import UserSession
from config.constants import ConversationState


class TestUserSession(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 12345
        self.username = "testuser"
        self.session = UserSession(user_id=self.user_id, username=self.username)
    
    def test_user_session_creation(self):
        """Test basic UserSession creation"""
        self.assertEqual(self.session.user_id, self.user_id)
        self.assertEqual(self.session.username, self.username)
        self.assertIsNone(self.session.current_state)
        self.assertIsNone(self.session.meetup_type)
        self.assertIsNone(self.session.location)
        self.assertIsNone(self.session.time)
        self.assertEqual(self.session.selected_friends, [])
        self.assertIsInstance(self.session.created_at, datetime)
        self.assertIsInstance(self.session.last_activity, datetime)
    
    def test_reset_current_meetup(self):
        """Test resetting meetup data"""
        # Set up some meetup data
        self.session.current_state = ConversationState.LOCATION
        self.session.meetup_type = "lunch"
        self.session.location = "Campus Café"
        self.session.time = "12:30 PM"
        self.session.selected_friends = ["Alex", "Sam"]
        
        original_activity = self.session.last_activity
        
        # Reset meetup
        self.session.reset_current_meetup()
        
        # Check that meetup data is cleared
        self.assertIsNone(self.session.current_state)
        self.assertIsNone(self.session.meetup_type)
        self.assertIsNone(self.session.location)
        self.assertIsNone(self.session.time)
        self.assertEqual(self.session.selected_friends, [])
        
        # Check that user data is preserved
        self.assertEqual(self.session.user_id, self.user_id)
        self.assertEqual(self.session.username, self.username)
        
        # Check that activity was updated
        self.assertGreater(self.session.last_activity, original_activity)
    
    def test_update_activity(self):
        """Test activity timestamp update"""
        original_activity = self.session.last_activity
        
        # Wait a tiny bit and update
        self.session.update_activity()
        
        self.assertGreaterEqual(self.session.last_activity, original_activity)
    
    def test_set_meetup_type(self):
        """Test setting meetup type"""
        original_activity = self.session.last_activity
        
        self.session.set_meetup_type("lunch")
        
        self.assertEqual(self.session.meetup_type, "lunch")
        self.assertGreater(self.session.last_activity, original_activity)
    
    def test_set_location(self):
        """Test setting location"""
        original_activity = self.session.last_activity
        
        self.session.set_location("Campus Café")
        
        self.assertEqual(self.session.location, "Campus Café")
        self.assertGreater(self.session.last_activity, original_activity)
    
    def test_set_time(self):
        """Test setting time"""
        original_activity = self.session.last_activity
        
        self.session.set_time("2:30 PM")
        
        self.assertEqual(self.session.time, "2:30 PM")
        self.assertGreater(self.session.last_activity, original_activity)
    
    def test_toggle_friend(self):
        """Test friend selection toggling"""
        # Add friend
        result = self.session.toggle_friend("Alex")
        self.assertTrue(result)
        self.assertIn("Alex", self.session.selected_friends)
        
        # Remove friend
        result = self.session.toggle_friend("Alex")
        self.assertFalse(result)
        self.assertNotIn("Alex", self.session.selected_friends)
        
        # Add multiple friends
        self.session.toggle_friend("Sam")
        self.session.toggle_friend("Jordan")
        self.assertEqual(len(self.session.selected_friends), 2)
        self.assertIn("Sam", self.session.selected_friends)
        self.assertIn("Jordan", self.session.selected_friends)
    
    def test_is_friend_selected(self):
        """Test friend selection checking"""
        self.assertFalse(self.session.is_friend_selected("Alex"))
        
        self.session.toggle_friend("Alex")
        self.assertTrue(self.session.is_friend_selected("Alex"))
        self.assertFalse(self.session.is_friend_selected("Sam"))
    
    def test_get_friends_display(self):
        """Test friends display formatting"""
        # No friends selected
        self.assertEqual(self.session.get_friends_display(), "None selected")
        
        # One friend
        self.session.toggle_friend("Alex")
        self.assertEqual(self.session.get_friends_display(), "Alex")
        
        # Multiple friends
        self.session.toggle_friend("Sam")
        self.session.toggle_friend("Jordan")
        display = self.session.get_friends_display()
        self.assertIn("Alex", display)
        self.assertIn("Sam", display)
        self.assertIn("Jordan", display)
        self.assertIn(",", display)
    
    def test_is_meetup_complete(self):
        """Test meetup completion checking"""
        # Empty session
        self.assertFalse(self.session.is_meetup_complete())
        
        # Only meetup type
        self.session.set_meetup_type("lunch")
        self.assertFalse(self.session.is_meetup_complete())
        
        # Meetup type and location
        self.session.set_location("Campus Café")
        self.assertFalse(self.session.is_meetup_complete())
        
        # All required fields
        self.session.toggle_friend("Alex")
        self.assertTrue(self.session.is_meetup_complete())
        
        # Time is optional
        self.session.set_time("2:30 PM")
        self.assertTrue(self.session.is_meetup_complete())
    
    def test_serialization(self):
        """Test dictionary serialization and deserialization"""
        # Set up session with data
        self.session.current_state = ConversationState.FRIENDS
        self.session.set_meetup_type("study")
        self.session.set_location("Library")
        self.session.set_time("3:00 PM")
        self.session.toggle_friend("Alex")
        self.session.toggle_friend("Sam")
        
        # Convert to dict
        data = self.session.to_dict()
        
        # Check dict structure
        self.assertEqual(data["user_id"], self.user_id)
        self.assertEqual(data["username"], self.username)
        self.assertEqual(data["current_state"], "friends")
        self.assertEqual(data["meetup_type"], "study")
        self.assertEqual(data["location"], "Library")
        self.assertEqual(data["time"], "3:00 PM")
        self.assertEqual(data["selected_friends"], ["Alex", "Sam"])
        
        # Recreate from dict
        restored_session = UserSession.from_dict(data)
        
        # Check restored session
        self.assertEqual(restored_session.user_id, self.session.user_id)
        self.assertEqual(restored_session.username, self.session.username)
        self.assertEqual(restored_session.current_state, self.session.current_state)
        self.assertEqual(restored_session.meetup_type, self.session.meetup_type)
        self.assertEqual(restored_session.location, self.session.location)
        self.assertEqual(restored_session.time, self.session.time)
        self.assertEqual(restored_session.selected_friends, self.session.selected_friends)


if __name__ == "__main__":
    unittest.main()