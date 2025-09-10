"""
Unit tests for StorageManager
"""

import json
import unittest
from datetime import datetime, timedelta
from storage.manager import StorageManager
from models.user_session import UserSession


class TestStorageManager(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.storage = StorageManager()
        self.user_id = 12345
        self.username = "testuser"
    
    def test_storage_manager_initialization(self):
        """Test StorageManager initialization"""
        self.assertEqual(self.storage.get_session_count(), 0)
        self.assertEqual(self.storage.get_ping_history_count(), 0)
        
        stats = self.storage.get_storage_stats()
        self.assertEqual(stats["active_sessions"], 0)
        self.assertEqual(stats["ping_records"], 0)
        self.assertIn("max_ping_history", stats)
    
    def test_get_user_session_new(self):
        """Test creating new user session"""
        session = self.storage.get_user_session(self.user_id, self.username)
        
        self.assertIsInstance(session, UserSession)
        self.assertEqual(session.user_id, self.user_id)
        self.assertEqual(session.username, self.username)
        self.assertEqual(self.storage.get_session_count(), 1)
    
    def test_get_user_session_existing(self):
        """Test retrieving existing user session"""
        # Create initial session
        session1 = self.storage.get_user_session(self.user_id, self.username)
        original_activity = session1.last_activity
        
        # Get same session again
        session2 = self.storage.get_user_session(self.user_id)
        
        # Should be the same session object
        self.assertIs(session1, session2)
        self.assertEqual(self.storage.get_session_count(), 1)
        
        # Activity should be updated
        self.assertGreaterEqual(session2.last_activity, original_activity)
    
    def test_get_user_session_username_update(self):
        """Test username update for existing session"""
        # Create session with initial username
        session = self.storage.get_user_session(self.user_id, "oldname")
        self.assertEqual(session.username, "oldname")
        
        # Update username
        updated_session = self.storage.get_user_session(self.user_id, "newname")
        
        # Should be same session with updated username
        self.assertIs(session, updated_session)
        self.assertEqual(updated_session.username, "newname")
    
    def test_update_user_session(self):
        """Test updating user session"""
        session = self.storage.get_user_session(self.user_id, self.username)
        original_activity = session.last_activity
        
        # Modify session
        session.set_meetup_type("lunch")
        
        # Update in storage
        self.storage.update_user_session(session)
        
        # Retrieve and verify
        retrieved_session = self.storage.get_user_session(self.user_id)
        self.assertEqual(retrieved_session.meetup_type, "lunch")
        self.assertGreater(retrieved_session.last_activity, original_activity)
    
    def test_remove_user_session(self):
        """Test removing user session"""
        # Create session
        self.storage.get_user_session(self.user_id, self.username)
        self.assertEqual(self.storage.get_session_count(), 1)
        
        # Remove session
        result = self.storage.remove_user_session(self.user_id)
        self.assertTrue(result)
        self.assertEqual(self.storage.get_session_count(), 0)
        
        # Try to remove non-existent session
        result = self.storage.remove_user_session(99999)
        self.assertFalse(result)
    
    def test_get_all_sessions(self):
        """Test getting all sessions"""
        # Create multiple sessions
        session1 = self.storage.get_user_session(12345, "user1")
        session2 = self.storage.get_user_session(67890, "user2")
        
        all_sessions = self.storage.get_all_sessions()
        
        self.assertEqual(len(all_sessions), 2)
        self.assertIn(12345, all_sessions)
        self.assertIn(67890, all_sessions)
        self.assertEqual(all_sessions[12345], session1)
        self.assertEqual(all_sessions[67890], session2)
        
        # Should be a copy, not the original dict
        all_sessions[99999] = UserSession(99999)
        self.assertEqual(self.storage.get_session_count(), 2)  # Original unchanged
    
    def test_cleanup_inactive_sessions(self):
        """Test cleanup of inactive sessions"""
        # Create sessions with different activity times
        session1 = self.storage.get_user_session(12345, "user1")
        session2 = self.storage.get_user_session(67890, "user2")
        
        # Make one session old
        old_time = datetime.now() - timedelta(hours=25)
        session1.last_activity = old_time
        
        # Cleanup sessions older than 24 hours
        cleaned_count = self.storage.cleanup_inactive_sessions(max_age_hours=24)
        
        self.assertEqual(cleaned_count, 1)
        self.assertEqual(self.storage.get_session_count(), 1)
        
        # Only the recent session should remain
        remaining_sessions = self.storage.get_all_sessions()
        self.assertIn(67890, remaining_sessions)
        self.assertNotIn(12345, remaining_sessions)
    
    def test_cleanup_inactive_sessions_none_old(self):
        """Test cleanup when no sessions are old"""
        # Create recent sessions
        self.storage.get_user_session(12345, "user1")
        self.storage.get_user_session(67890, "user2")
        
        # Cleanup - should remove nothing
        cleaned_count = self.storage.cleanup_inactive_sessions(max_age_hours=1)
        
        self.assertEqual(cleaned_count, 0)
        self.assertEqual(self.storage.get_session_count(), 2)
    
    def test_clear_all_data(self):
        """Test clearing all data"""
        # Create some data
        self.storage.get_user_session(12345, "user1")
        self.storage.get_user_session(67890, "user2")
        
        self.assertEqual(self.storage.get_session_count(), 2)
        
        # Clear all data
        self.storage.clear_all_data()
        
        self.assertEqual(self.storage.get_session_count(), 0)
        self.assertEqual(self.storage.get_ping_history_count(), 0)
    
    def test_string_representations(self):
        """Test string and repr methods"""
        # Empty storage
        str_repr = str(self.storage)
        self.assertIn("StorageManager", str_repr)
        self.assertIn("sessions=0", str_repr)
        self.assertIn("pings=0", str_repr)
        
        repr_str = repr(self.storage)
        self.assertIn("StorageManager", repr_str)
        self.assertIn("max_history", repr_str)
        
        # With data
        self.storage.get_user_session(12345, "user1")
        str_repr = str(self.storage)
        self.assertIn("sessions=1", str_repr)


if __name__ == "__main__":
    unittest.main()
    
def test_save_ping(self):
        """Test saving ping records"""
        from models.ping import PingRecord
        
        ping = PingRecord(
            organizer_id=12345,
            organizer_name="Alice",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["Bob", "Charlie"]
        )
        
        self.storage.save_ping(ping)
        
        self.assertEqual(self.storage.get_ping_history_count(), 1)
        
        # Save another ping
        ping2 = PingRecord(
            organizer_id=67890,
            organizer_name="Bob",
            meetup_type="study",
            location="Library",
            time="2:00 PM",
            invited_friends=["Alice"]
        )
        
        self.storage.save_ping(ping2)
        self.assertEqual(self.storage.get_ping_history_count(), 2)
    
    def test_save_ping_history_limit(self):
        """Test ping history limit enforcement"""
        from models.ping import PingRecord
        
        # Set a small limit for testing
        self.storage._max_ping_history = 3
        
        # Add more pings than the limit
        for i in range(5):
            ping = PingRecord(
                organizer_id=12345,
                organizer_name=f"User{i}",
                meetup_type="lunch",
                location="Campus Café",
                time="12:30 PM",
                invited_friends=["Friend"]
            )
            self.storage.save_ping(ping)
        
        # Should only keep the limit
        self.assertEqual(self.storage.get_ping_history_count(), 3)
    
    def test_get_recent_pings(self):
        """Test retrieving recent pings"""
        from models.ping import PingRecord
        from datetime import datetime, timedelta
        
        # Create pings with different timestamps
        base_time = datetime.now()
        
        ping1 = PingRecord(
            organizer_id=12345,
            organizer_name="Alice",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["Bob"]
        )
        ping1.timestamp = base_time - timedelta(hours=2)
        
        ping2 = PingRecord(
            organizer_id=67890,
            organizer_name="Bob",
            meetup_type="study",
            location="Library",
            time="2:00 PM",
            invited_friends=["Alice"]
        )
        ping2.timestamp = base_time - timedelta(hours=1)
        
        ping3 = PingRecord(
            organizer_id=11111,
            organizer_name="Charlie",
            meetup_type="lunch",
            location="Food Court",
            time="1:00 PM",
            invited_friends=["Alice", "Bob"]
        )
        ping3.timestamp = base_time
        
        # Save pings
        self.storage.save_ping(ping1)
        self.storage.save_ping(ping2)
        self.storage.save_ping(ping3)
        
        # Get recent pings
        recent = self.storage.get_recent_pings(limit=2)
        
        self.assertEqual(len(recent), 2)
        # Should be in reverse chronological order (newest first)
        self.assertEqual(recent[0].organizer_name, "Charlie")
        self.assertEqual(recent[1].organizer_name, "Bob")
        
        # Test default limit
        all_recent = self.storage.get_recent_pings()
        self.assertEqual(len(all_recent), 3)
    
    def test_get_pings_by_organizer(self):
        """Test getting pings by specific organizer"""
        from models.ping import PingRecord
        
        # Create pings by different organizers
        ping1 = PingRecord(
            organizer_id=12345,
            organizer_name="Alice",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["Bob"]
        )
        
        ping2 = PingRecord(
            organizer_id=67890,
            organizer_name="Bob",
            meetup_type="study",
            location="Library",
            time="2:00 PM",
            invited_friends=["Alice"]
        )
        
        ping3 = PingRecord(
            organizer_id=12345,
            organizer_name="Alice",
            meetup_type="study",
            location="Study Hall",
            time="3:00 PM",
            invited_friends=["Charlie"]
        )
        
        self.storage.save_ping(ping1)
        self.storage.save_ping(ping2)
        self.storage.save_ping(ping3)
        
        # Get Alice's pings
        alice_pings = self.storage.get_pings_by_organizer(12345)
        self.assertEqual(len(alice_pings), 2)
        
        # Get Bob's pings
        bob_pings = self.storage.get_pings_by_organizer(67890)
        self.assertEqual(len(bob_pings), 1)
        self.assertEqual(bob_pings[0].organizer_name, "Bob")
        
        # Test with limit
        alice_limited = self.storage.get_pings_by_organizer(12345, limit=1)
        self.assertEqual(len(alice_limited), 1)
    
    def test_get_pings_by_criteria(self):
        """Test getting pings by criteria"""
        from models.ping import PingRecord
        
        # Create pings with different criteria
        ping1 = PingRecord(
            organizer_id=12345,
            organizer_name="Alice",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["Bob"]
        )
        
        ping2 = PingRecord(
            organizer_id=67890,
            organizer_name="Bob",
            meetup_type="study",
            location="Library",
            time="2:00 PM",
            invited_friends=["Alice"]
        )
        
        ping3 = PingRecord(
            organizer_id=11111,
            organizer_name="Charlie",
            meetup_type="lunch",
            location="Food Court",
            time="1:00 PM",
            invited_friends=["Alice"]
        )
        
        self.storage.save_ping(ping1)
        self.storage.save_ping(ping2)
        self.storage.save_ping(ping3)
        
        # Filter by meetup type
        lunch_pings = self.storage.get_pings_by_criteria(meetup_type="lunch")
        self.assertEqual(len(lunch_pings), 2)
        
        study_pings = self.storage.get_pings_by_criteria(meetup_type="study")
        self.assertEqual(len(study_pings), 1)
        
        # Filter by location
        cafe_pings = self.storage.get_pings_by_criteria(location="Campus Café")
        self.assertEqual(len(cafe_pings), 1)
        
        # Filter by both criteria
        lunch_cafe = self.storage.get_pings_by_criteria(
            meetup_type="lunch", 
            location="Campus Café"
        )
        self.assertEqual(len(lunch_cafe), 1)
        
        # No matching criteria
        no_match = self.storage.get_pings_by_criteria(
            meetup_type="lunch", 
            location="Library"
        )
        self.assertEqual(len(no_match), 0)
        
        # Test with limit
        limited = self.storage.get_pings_by_criteria(meetup_type="lunch", limit=1)
        self.assertEqual(len(limited), 1)
    
    def test_cleanup_old_pings(self):
        """Test cleanup of old ping records"""
        from models.ping import PingRecord
        from datetime import datetime, timedelta
        
        base_time = datetime.now()
        
        # Create old and recent pings
        old_ping = PingRecord(
            organizer_id=12345,
            organizer_name="Alice",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["Bob"]
        )
        old_ping.timestamp = base_time - timedelta(days=35)
        
        recent_ping = PingRecord(
            organizer_id=67890,
            organizer_name="Bob",
            meetup_type="study",
            location="Library",
            time="2:00 PM",
            invited_friends=["Alice"]
        )
        recent_ping.timestamp = base_time - timedelta(days=5)
        
        self.storage.save_ping(old_ping)
        self.storage.save_ping(recent_ping)
        
        self.assertEqual(self.storage.get_ping_history_count(), 2)
        
        # Cleanup pings older than 30 days
        cleaned_count = self.storage.cleanup_old_pings(max_age_days=30)
        
        self.assertEqual(cleaned_count, 1)
        self.assertEqual(self.storage.get_ping_history_count(), 1)
        
        # Remaining ping should be the recent one
        remaining_pings = self.storage.get_recent_pings()
        self.assertEqual(len(remaining_pings), 1)
        self.assertEqual(remaining_pings[0].organizer_name, "Bob")
    
    def test_clear_ping_history(self):
        """Test clearing ping history"""
        from models.ping import PingRecord
        
        # Add some pings
        ping1 = PingRecord(
            organizer_id=12345,
            organizer_name="Alice",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["Bob"]
        )
        
        ping2 = PingRecord(
            organizer_id=67890,
            organizer_name="Bob",
            meetup_type="study",
            location="Library",
            time="2:00 PM",
            invited_friends=["Alice"]
        )
        
        self.storage.save_ping(ping1)
        self.storage.save_ping(ping2)
        
        self.assertEqual(self.storage.get_ping_history_count(), 2)
        
        # Clear history
        cleared_count = self.storage.clear_ping_history()
        
        self.assertEqual(cleared_count, 2)
        self.assertEqual(self.storage.get_ping_history_count(), 0)
        
        # Recent pings should be empty
        recent = self.storage.get_recent_pings()
        self.assertEqual(len(recent), 0)    de
f test_persist_to_file(self):
        """Test persisting data to file"""
        import tempfile
        import os
        from models.ping import PingRecord
        
        # Create some test data
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        
        ping = PingRecord(
            organizer_id=12345,
            organizer_name="testuser",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["Alice", "Bob"]
        )
        self.storage.save_ping(ping)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            # Persist to file
            result = self.storage.persist_to_file(temp_path)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify file content
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            self.assertIn("sessions", data)
            self.assertIn("ping_history", data)
            self.assertIn("metadata", data)
            
            # Check session data
            self.assertIn("12345", data["sessions"])
            session_data = data["sessions"]["12345"]
            self.assertEqual(session_data["meetup_type"], "lunch")
            self.assertEqual(session_data["location"], "Campus Café")
            
            # Check ping data
            self.assertEqual(len(data["ping_history"]), 1)
            ping_data = data["ping_history"][0]
            self.assertEqual(ping_data["organizer_name"], "testuser")
            self.assertEqual(ping_data["meetup_type"], "lunch")
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_load_from_file(self):
        """Test loading data from file"""
        import tempfile
        import os
        from models.ping import PingRecord
        
        # Create test data
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("study")
        session.set_location("Library")
        
        ping = PingRecord(
            organizer_id=12345,
            organizer_name="testuser",
            meetup_type="study",
            location="Library",
            time="2:00 PM",
            invited_friends=["Charlie"]
        )
        self.storage.save_ping(ping)
        
        # Create temporary file and persist
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            # Save data
            self.storage.persist_to_file(temp_path)
            
            # Create new storage manager and load data
            new_storage = StorageManager()
            result = new_storage.load_from_file(temp_path)
            
            self.assertTrue(result)
            self.assertEqual(new_storage.get_session_count(), 1)
            self.assertEqual(new_storage.get_ping_history_count(), 1)
            
            # Verify loaded session
            loaded_session = new_storage.get_user_session(12345)
            self.assertEqual(loaded_session.username, "testuser")
            self.assertEqual(loaded_session.meetup_type, "study")
            self.assertEqual(loaded_session.location, "Library")
            
            # Verify loaded ping
            loaded_pings = new_storage.get_recent_pings()
            self.assertEqual(len(loaded_pings), 1)
            loaded_ping = loaded_pings[0]
            self.assertEqual(loaded_ping.organizer_name, "testuser")
            self.assertEqual(loaded_ping.meetup_type, "study")
            self.assertEqual(loaded_ping.location, "Library")
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file"""
        result = self.storage.load_from_file("/nonexistent/path/file.json")
        self.assertFalse(result)
        
        # Storage should remain empty
        self.assertEqual(self.storage.get_session_count(), 0)
        self.assertEqual(self.storage.get_ping_history_count(), 0)
    
    def test_load_from_invalid_json(self):
        """Test loading from file with invalid JSON"""
        import tempfile
        import os
        
        # Create file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("{ invalid json content")
            temp_path = f.name
        
        try:
            result = self.storage.load_from_file(temp_path)
            self.assertFalse(result)
            
            # Storage should remain empty
            self.assertEqual(self.storage.get_session_count(), 0)
            self.assertEqual(self.storage.get_ping_history_count(), 0)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_persist_load_roundtrip(self):
        """Test complete persist and load roundtrip"""
        import tempfile
        import os
        from models.ping import PingRecord
        
        # Create complex test data
        session1 = self.storage.get_user_session(12345, "alice")
        session1.set_meetup_type("lunch")
        session1.set_location("Campus Café")
        session1.toggle_friend("Bob")
        session1.toggle_friend("Charlie")
        
        session2 = self.storage.get_user_session(67890, "bob")
        session2.set_meetup_type("study")
        session2.set_location("Library")
        
        ping1 = PingRecord(
            organizer_id=12345,
            organizer_name="alice",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["Bob", "Charlie"]
        )
        
        ping2 = PingRecord(
            organizer_id=67890,
            organizer_name="bob",
            meetup_type="study",
            location="Library",
            time="",
            invited_friends=["Alice", "Diana"]
        )
        
        self.storage.save_ping(ping1)
        self.storage.save_ping(ping2)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            # Persist and load
            self.assertTrue(self.storage.persist_to_file(temp_path))
            
            new_storage = StorageManager()
            self.assertTrue(new_storage.load_from_file(temp_path))
            
            # Verify all data is preserved
            self.assertEqual(new_storage.get_session_count(), 2)
            self.assertEqual(new_storage.get_ping_history_count(), 2)
            
            # Check sessions
            alice_session = new_storage.get_user_session(12345)
            self.assertEqual(alice_session.username, "alice")
            self.assertEqual(alice_session.meetup_type, "lunch")
            self.assertEqual(alice_session.selected_friends, ["Bob", "Charlie"])
            
            bob_session = new_storage.get_user_session(67890)
            self.assertEqual(bob_session.username, "bob")
            self.assertEqual(bob_session.meetup_type, "study")
            
            # Check pings
            recent_pings = new_storage.get_recent_pings()
            self.assertEqual(len(recent_pings), 2)
            
            # Find specific pings
            alice_ping = next(p for p in recent_pings if p.organizer_name == "alice")
            bob_ping = next(p for p in recent_pings if p.organizer_name == "bob")
            
            self.assertEqual(alice_ping.invited_friends, ["Bob", "Charlie"])
            self.assertEqual(bob_ping.invited_friends, ["Alice", "Diana"])
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_create_backup(self):
        """Test creating backup files"""
        import tempfile
        import os
        from models.ping import PingRecord
        
        # Create some data and persist it
        session = self.storage.get_user_session(12345, "testuser")
        ping = PingRecord(
            organizer_id=12345,
            organizer_name="testuser",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["Alice"]
        )
        self.storage.save_ping(ping)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            # Persist data
            self.storage.persist_to_file(temp_path)
            
            # Create backup
            backup_path = self.storage.create_backup(temp_path)
            
            self.assertNotEqual(backup_path, "")
            self.assertTrue(os.path.exists(backup_path))
            self.assertIn("backup_", backup_path)
            
            # Verify backup content matches original
            with open(temp_path, 'r') as f:
                original_content = f.read()
            
            with open(backup_path, 'r') as f:
                backup_content = f.read()
            
            self.assertEqual(original_content, backup_content)
            
            # Clean up backup
            if os.path.exists(backup_path):
                os.unlink(backup_path)
                
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_create_backup_nonexistent_file(self):
        """Test creating backup of non-existent file"""
        backup_path = self.storage.create_backup("/nonexistent/file.json")
        self.assertEqual(backup_path, "")