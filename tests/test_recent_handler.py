"""
Unit tests for RecentHandler
"""

import unittest
from unittest.mock import Mock, AsyncMock
import asyncio
from datetime import datetime, timedelta

from handlers.recent import RecentHandler, recent_command, ping_statistics_command
from storage.manager import StorageManager
from models.ping import PingRecord


class TestRecentHandler(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.storage = StorageManager()
        self.handler = RecentHandler(self.storage)
        
        # Mock update and context
        self.mock_update = Mock()
        self.mock_context = Mock()
        
        # Mock user
        self.mock_user = Mock()
        self.mock_user.id = 12345
        self.mock_user.username = "testuser"
        
        # Mock message
        self.mock_message = Mock()
        self.mock_message.reply_text = AsyncMock()
        
        # Mock chat
        self.mock_chat = Mock()
        self.mock_chat.id = 67890
        
        # Set up update
        self.mock_update.effective_user = self.mock_user
        self.mock_update.effective_chat = self.mock_chat
        self.mock_update.message = self.mock_message
        
        # Mock bot for typing action
        self.mock_context.bot = Mock()
        self.mock_context.bot.send_chat_action = AsyncMock()
        
        # Create some test pings
        self._create_test_pings()
    
    def _create_test_pings(self):
        """Create test ping records"""
        # Recent lunch ping
        lunch_ping = PingRecord(
            organizer_id=11111,
            organizer_name="alice",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["bob", "charlie"]
        )
        lunch_ping.timestamp = datetime.now() - timedelta(hours=1)
        self.storage.save_ping(lunch_ping)
        
        # Recent study ping
        study_ping = PingRecord(
            organizer_id=22222,
            organizer_name="bob",
            meetup_type="study",
            location="Library",
            time="2:00 PM",
            invited_friends=["alice", "diana"]
        )
        study_ping.timestamp = datetime.now() - timedelta(hours=2)
        self.storage.save_ping(study_ping)
        
        # Older ping
        old_ping = PingRecord(
            organizer_id=33333,
            organizer_name="charlie",
            meetup_type="lunch",
            location="Food Court",
            time="",
            invited_friends=["alice"]
        )
        old_ping.timestamp = datetime.now() - timedelta(days=1)
        self.storage.save_ping(old_ping)
    
    def test_handler_initialization(self):
        """Test RecentHandler initialization"""
        self.assertEqual(self.handler.storage, self.storage)
        self.assertIsNotNone(self.handler.logger)
    
    async def test_recent_command_success(self):
        """Test successful recent command"""
        await self.handler.recent_command(self.mock_update, self.mock_context)
        
        # Should send typing action
        self.mock_context.bot.send_chat_action.assert_called_once()
        
        # Should send message with recent pings
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        
        # Should contain recent pings info
        self.assertIn("Recent Invitations", sent_message)
        self.assertIn("alice", sent_message)
        self.assertIn("bob", sent_message)
        self.assertIn("lunch", sent_message)
        self.assertIn("study", sent_message)
    
    async def test_recent_command_no_pings(self):
        """Test recent command with no pings"""
        # Clear all pings
        self.storage.clear_ping_history()
        
        await self.handler.recent_command(self.mock_update, self.mock_context)
        
        # Should send message about no pings
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("No recent invitations", sent_message)
    
    async def test_recent_command_no_user_id(self):
        """Test recent command with no user ID"""
        self.mock_update.effective_user = None
        
        await self.handler.recent_command(self.mock_update, self.mock_context)
        
        # Should handle error gracefully
        self.mock_message.reply_text.assert_called_once()
    
    async def test_get_user_recent_pings(self):
        """Test getting pings by specific user"""
        # Add ping by test user
        user_ping = PingRecord(
            organizer_id=12345,
            organizer_name="testuser",
            meetup_type="lunch",
            location="Campus Café",
            time="1:00 PM",
            invited_friends=["friend1"]
        )
        self.storage.save_ping(user_ping)
        
        pings = await self.handler.get_user_recent_pings(12345)
        
        # Should return only pings by this user
        self.assertEqual(len(pings), 1)
        self.assertEqual(pings[0].organizer_id, 12345)
        self.assertEqual(pings[0].organizer_name, "testuser")
    
    async def test_get_user_recent_pings_with_limit(self):
        """Test getting user pings with limit"""
        # Add multiple pings by same user
        for i in range(3):
            ping = PingRecord(
                organizer_id=12345,
                organizer_name="testuser",
                meetup_type="lunch",
                location=f"Location {i}",
                time="1:00 PM",
                invited_friends=["friend1"]
            )
            self.storage.save_ping(ping)
        
        pings = await self.handler.get_user_recent_pings(12345, limit=2)
        
        # Should return only 2 pings
        self.assertEqual(len(pings), 2)
    
    async def test_get_recent_pings_by_type(self):
        """Test getting pings by meetup type"""
        lunch_pings = await self.handler.get_recent_pings_by_type("lunch")
        study_pings = await self.handler.get_recent_pings_by_type("study")
        
        # Should filter by type
        self.assertGreater(len(lunch_pings), 0)
        self.assertGreater(len(study_pings), 0)
        
        # All lunch pings should be lunch type
        for ping in lunch_pings:
            self.assertEqual(ping.meetup_type, "lunch")
        
        # All study pings should be study type
        for ping in study_pings:
            self.assertEqual(ping.meetup_type, "study")
    
    async def test_get_recent_pings_by_location(self):
        """Test getting pings by location"""
        cafe_pings = await self.handler.get_recent_pings_by_location("Campus Café")
        library_pings = await self.handler.get_recent_pings_by_location("Library")
        
        # Should filter by location
        self.assertGreater(len(cafe_pings), 0)
        self.assertGreater(len(library_pings), 0)
        
        # All cafe pings should be at Campus Café
        for ping in cafe_pings:
            self.assertEqual(ping.location, "Campus Café")
        
        # All library pings should be at Library
        for ping in library_pings:
            self.assertEqual(ping.location, "Library")
    
    def test_get_ping_statistics(self):
        """Test getting ping statistics"""
        stats = self.handler.get_ping_statistics()
        
        # Should return valid statistics
        self.assertIn("total_pings", stats)
        self.assertIn("lunch_pings", stats)
        self.assertIn("study_pings", stats)
        self.assertIn("unique_organizers", stats)
        self.assertIn("unique_locations", stats)
        self.assertIn("most_popular_location", stats)
        
        # Should have correct counts
        self.assertEqual(stats["total_pings"], 3)  # From _create_test_pings
        self.assertEqual(stats["lunch_pings"], 2)
        self.assertEqual(stats["study_pings"], 1)
        self.assertEqual(stats["unique_organizers"], 3)
        
        # Should have locations
        self.assertIsInstance(stats["unique_locations"], set)
        self.assertIn("Campus Café", stats["unique_locations"])
        self.assertIn("Library", stats["unique_locations"])
    
    def test_get_ping_statistics_no_pings(self):
        """Test getting statistics with no pings"""
        # Clear all pings
        self.storage.clear_ping_history()
        
        stats = self.handler.get_ping_statistics()
        
        # Should return zero statistics
        self.assertEqual(stats["total_pings"], 0)
        self.assertEqual(stats["lunch_pings"], 0)
        self.assertEqual(stats["study_pings"], 0)
        self.assertEqual(stats["unique_organizers"], 0)
        self.assertIsNone(stats["most_popular_location"])
    
    async def test_send_ping_statistics(self):
        """Test sending ping statistics"""
        await self.handler.send_ping_statistics(self.mock_update, self.mock_context)
        
        # Should send statistics message
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        
        # Should contain statistics
        self.assertIn("UniLinkUp Statistics", sent_message)
        self.assertIn("Total invitations", sent_message)
        self.assertIn("Lunch meetups", sent_message)
        self.assertIn("Study sessions", sent_message)
    
    async def test_cleanup_old_pings(self):
        """Test cleaning up old pings"""
        # Should have 3 pings initially
        initial_count = self.storage.get_ping_history_count()
        self.assertEqual(initial_count, 3)
        
        # Cleanup pings older than 12 hours (should remove the 1-day old ping)
        cleaned_count = await self.handler.cleanup_old_pings(max_age_days=0.5)
        
        # Should clean up 1 ping
        self.assertEqual(cleaned_count, 1)
        
        # Should have 2 pings remaining
        remaining_count = self.storage.get_ping_history_count()
        self.assertEqual(remaining_count, 2)


class TestStandaloneFunctions(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.storage = StorageManager()
        
        # Mock update and context
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_context.bot_data = {'storage_manager': self.storage}
        
        # Mock user and message
        self.mock_user = Mock()
        self.mock_user.id = 12345
        self.mock_user.username = "testuser"
        
        self.mock_message = Mock()
        self.mock_message.reply_text = AsyncMock()
        
        self.mock_update.effective_user = self.mock_user
        self.mock_update.message = self.mock_message
        
        # Mock bot
        self.mock_context.bot = Mock()
        self.mock_context.bot.send_chat_action = AsyncMock()
        
        # Add a test ping
        ping = PingRecord(
            organizer_id=11111,
            organizer_name="alice",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=["bob"]
        )
        self.storage.save_ping(ping)
    
    async def test_standalone_recent_command(self):
        """Test standalone recent command function"""
        await recent_command(self.mock_update, self.mock_context)
        
        # Should send message with recent pings
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("Recent Invitations", sent_message)
    
    async def test_standalone_ping_statistics_command(self):
        """Test standalone ping statistics command function"""
        await ping_statistics_command(self.mock_update, self.mock_context)
        
        # Should send statistics message
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("UniLinkUp Statistics", sent_message)
    
    async def test_standalone_commands_no_storage(self):
        """Test standalone commands with no storage manager"""
        self.mock_context.bot_data = {}
        
        # Test recent command
        await recent_command(self.mock_update, self.mock_context)
        self.mock_message.reply_text.assert_called()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("configuration error", sent_message)
        
        # Reset mock
        self.mock_message.reply_text.reset_mock()
        
        # Test statistics command
        await ping_statistics_command(self.mock_update, self.mock_context)
        self.mock_message.reply_text.assert_called()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("configuration error", sent_message)


# Helper function to run async tests
def run_async_test(coro):
    """Helper to run async test methods"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Patch async test methods
for cls in [TestRecentHandler, TestStandaloneFunctions]:
    for method_name in dir(cls):
        if method_name.startswith('test_') and 'async' in method_name:
            method = getattr(cls, method_name)
            if asyncio.iscoroutinefunction(method):
                setattr(cls, method_name, 
                       lambda self, m=method: run_async_test(m(self)))


if __name__ == "__main__":
    unittest.main()