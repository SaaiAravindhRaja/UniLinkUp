"""
Unit tests for PingRecord model
"""

import unittest
from datetime import datetime, timedelta
from models.ping import PingRecord


class TestPingRecord(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.organizer_id = 12345
        self.organizer_name = "Alice"
        self.meetup_type = "lunch"
        self.location = "Campus Café"
        self.time = "12:30 PM"
        self.invited_friends = ["Bob", "Charlie", "Diana"]
        
        self.ping = PingRecord(
            organizer_id=self.organizer_id,
            organizer_name=self.organizer_name,
            meetup_type=self.meetup_type,
            location=self.location,
            time=self.time,
            invited_friends=self.invited_friends.copy()
        )
    
    def test_ping_record_creation(self):
        """Test basic PingRecord creation"""
        self.assertEqual(self.ping.organizer_id, self.organizer_id)
        self.assertEqual(self.ping.organizer_name, self.organizer_name)
        self.assertEqual(self.ping.meetup_type, self.meetup_type)
        self.assertEqual(self.ping.location, self.location)
        self.assertEqual(self.ping.time, self.time)
        self.assertEqual(self.ping.invited_friends, self.invited_friends)
        self.assertIsInstance(self.ping.timestamp, datetime)
    
    def test_format_for_display(self):
        """Test display formatting"""
        display = self.ping.format_for_display()
        
        # Check that all key information is included
        self.assertIn("🍽️", display)  # Lunch emoji
        self.assertIn("Lunch", display)
        self.assertIn(self.location, display)
        self.assertIn(self.time, display)
        self.assertIn(self.organizer_name, display)
        
        # Check that friends are included
        for friend in self.invited_friends:
            self.assertIn(friend, display)
    
    def test_format_for_display_study(self):
        """Test display formatting for study session"""
        study_ping = PingRecord(
            organizer_id=self.organizer_id,
            organizer_name=self.organizer_name,
            meetup_type="study",
            location="Library",
            time="2:00 PM",
            invited_friends=["Bob"]
        )
        
        display = study_ping.format_for_display()
        
        self.assertIn("📚", display)  # Study emoji
        self.assertIn("Study", display)
        self.assertIn("Library", display)
    
    def test_format_for_display_flexible_time(self):
        """Test display formatting with no specific time"""
        flexible_ping = PingRecord(
            organizer_id=self.organizer_id,
            organizer_name=self.organizer_name,
            meetup_type="lunch",
            location=self.location,
            time="",  # No specific time
            invited_friends=self.invited_friends.copy()
        )
        
        display = flexible_ping.format_for_display()
        self.assertIn("Flexible time", display)
    
    def test_format_for_display_long_friends_list(self):
        """Test display formatting with long friends list"""
        long_friends = [f"Friend{i}" for i in range(10)]
        long_ping = PingRecord(
            organizer_id=self.organizer_id,
            organizer_name=self.organizer_name,
            meetup_type="lunch",
            location=self.location,
            time=self.time,
            invited_friends=long_friends
        )
        
        display = long_ping.format_for_display()
        # Should truncate long friends list
        self.assertIn("...", display)
    
    def test_get_short_summary(self):
        """Test short summary generation"""
        summary = self.ping.get_short_summary()
        
        self.assertIn("🍽️", summary)
        self.assertIn("Lunch", summary)
        self.assertIn(self.location, summary)
        self.assertIn("3 friends", summary)  # Count of friends
    
    def test_get_friends_except(self):
        """Test getting friends list excluding one"""
        other_friends = self.ping.get_friends_except("Bob")
        
        self.assertNotIn("Bob", other_friends)
        self.assertIn("Charlie", other_friends)
        self.assertIn("Diana", other_friends)
        self.assertEqual(len(other_friends), 2)
        
        # Test with non-existent friend
        all_friends = self.ping.get_friends_except("NonExistent")
        self.assertEqual(len(all_friends), 3)
    
    def test_get_other_friends_display(self):
        """Test other friends display formatting"""
        # Exclude one friend
        display = self.ping.get_other_friends_display("Bob")
        self.assertNotIn("Bob", display)
        self.assertIn("Charlie", display)
        self.assertIn("Diana", display)
        
        # Test with single friend ping
        single_ping = PingRecord(
            organizer_id=self.organizer_id,
            organizer_name=self.organizer_name,
            meetup_type="lunch",
            location=self.location,
            time=self.time,
            invited_friends=["Bob"]
        )
        
        display = single_ping.get_other_friends_display("Bob")
        self.assertEqual(display, "No other friends")
        
        # Test with two friends
        two_friends_ping = PingRecord(
            organizer_id=self.organizer_id,
            organizer_name=self.organizer_name,
            meetup_type="lunch",
            location=self.location,
            time=self.time,
            invited_friends=["Bob", "Charlie"]
        )
        
        display = two_friends_ping.get_other_friends_display("Bob")
        self.assertEqual(display, "Charlie")
    
    def test_matches_criteria(self):
        """Test criteria matching"""
        # Test meetup type matching
        self.assertTrue(self.ping.matches_criteria(meetup_type="lunch"))
        self.assertFalse(self.ping.matches_criteria(meetup_type="study"))
        
        # Test location matching
        self.assertTrue(self.ping.matches_criteria(location="Campus Café"))
        self.assertFalse(self.ping.matches_criteria(location="Library"))
        
        # Test combined criteria
        self.assertTrue(self.ping.matches_criteria(
            meetup_type="lunch", 
            location="Campus Café"
        ))
        self.assertFalse(self.ping.matches_criteria(
            meetup_type="study", 
            location="Campus Café"
        ))
        
        # Test no criteria (should match)
        self.assertTrue(self.ping.matches_criteria())
    
    def test_serialization(self):
        """Test dictionary serialization and deserialization"""
        # Convert to dict
        data = self.ping.to_dict()
        
        # Check dict structure
        self.assertEqual(data["organizer_id"], self.organizer_id)
        self.assertEqual(data["organizer_name"], self.organizer_name)
        self.assertEqual(data["meetup_type"], self.meetup_type)
        self.assertEqual(data["location"], self.location)
        self.assertEqual(data["time"], self.time)
        self.assertEqual(data["invited_friends"], self.invited_friends)
        self.assertIn("timestamp", data)
        
        # Recreate from dict
        restored_ping = PingRecord.from_dict(data)
        
        # Check restored ping
        self.assertEqual(restored_ping.organizer_id, self.ping.organizer_id)
        self.assertEqual(restored_ping.organizer_name, self.ping.organizer_name)
        self.assertEqual(restored_ping.meetup_type, self.ping.meetup_type)
        self.assertEqual(restored_ping.location, self.ping.location)
        self.assertEqual(restored_ping.time, self.ping.time)
        self.assertEqual(restored_ping.invited_friends, self.ping.invited_friends)
        # Timestamps should be very close (within a second)
        time_diff = abs((restored_ping.timestamp - self.ping.timestamp).total_seconds())
        self.assertLess(time_diff, 1.0)
    
    def test_string_representations(self):
        """Test string and repr methods"""
        str_repr = str(self.ping)
        self.assertIn("Lunch", str_repr)
        self.assertIn(self.location, str_repr)
        
        repr_str = repr(self.ping)
        self.assertIn("PingRecord", repr_str)
        self.assertIn(self.organizer_name, repr_str)
        self.assertIn(self.meetup_type, repr_str)


if __name__ == "__main__":
    unittest.main()