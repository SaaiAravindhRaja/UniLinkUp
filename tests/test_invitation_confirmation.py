"""
Unit tests for invitation confirmation and notification
"""

import unittest
from unittest.mock import Mock, AsyncMock
import asyncio
from telegram.ext import ConversationHandler

from handlers.meetup import MeetupHandler, confirm_invitation
from storage.manager import StorageManager
from config.constants import ConversationState, FRIENDS
from models.ping import PingRecord


class TestInvitationConfirmation(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.storage = StorageManager()
        self.handler = MeetupHandler(self.storage)
        
        # Mock update and context
        self.mock_update = Mock()
        self.mock_context = Mock()
        
        # Mock user
        self.mock_user = Mock()
        self.mock_user.id = 12345
        self.mock_user.username = "testuser"
        
        # Mock callback query
        self.mock_callback = Mock()
        self.mock_callback.data = "confirm_send"
        self.mock_callback.answer = AsyncMock()
        self.mock_callback.message = Mock()
        self.mock_callback.message.edit_text = AsyncMock()
        self.mock_callback.message.reply_text = AsyncMock()
        
        # Set up update
        self.mock_update.effective_user = self.mock_user
        self.mock_update.callback_query = self.mock_callback
        
        # Create complete session
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        session.set_time("12:30 PM")
        session.toggle_friend(FRIENDS[0])
        session.toggle_friend(FRIENDS[1])
        session.current_state = ConversationState.CONFIRM
        self.storage.update_user_session(session)
    
    async def test_confirm_invitation_send_success(self):
        """Test successful invitation sending"""
        result = await self.handler.confirm_invitation(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
        
        # Should create ping record
        pings = self.storage.get_recent_pings(limit=1)
        self.assertEqual(len(pings), 1)
        
        ping = pings[0]
        self.assertEqual(ping.organizer_id, 12345)
        self.assertEqual(ping.organizer_name, "testuser")
        self.assertEqual(ping.meetup_type, "lunch")
        self.assertEqual(ping.location, "Campus Café")
        self.assertEqual(ping.time, "12:30 PM")
        self.assertEqual(len(ping.invited_friends), 2)
        self.assertIn(FRIENDS[0], ping.invited_friends)
        self.assertIn(FRIENDS[1], ping.invited_friends)
        
        # Should edit message with success
        self.mock_callback.message.edit_text.assert_called_once()
        sent_message = self.mock_callback.message.edit_text.call_args[0][0]
        self.assertIn("sent successfully", sent_message)
        self.assertIn("Notifications sent", sent_message)
        
        # Should answer callback
        self.mock_callback.answer.assert_called_once()
        
        # Session should be cleaned up
        updated_session = self.storage.get_user_session(12345)
        self.assertIsNone(updated_session.meetup_type)
    
    async def test_confirm_invitation_cancel(self):
        """Test cancelling invitation"""
        self.mock_callback.data = "confirm_cancel"
        
        result = await self.handler.confirm_invitation(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
        
        # Should not create ping record
        pings = self.storage.get_recent_pings()
        self.assertEqual(len(pings), 0)
        
        # Should send cancellation message
        self.mock_callback.message.reply_text.assert_called_once()
        sent_message = self.mock_callback.message.reply_text.call_args[0][0]
        self.assertIn("cancelled", sent_message.lower())
    
    async def test_confirm_invitation_incomplete_session(self):
        """Test confirmation with incomplete session"""
        # Remove required data
        session = self.storage.get_user_session(12345)
        session.selected_friends = []  # No friends selected
        self.storage.update_user_session(session)
        
        result = await self.handler.confirm_invitation(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
        
        # Should not create ping record
        pings = self.storage.get_recent_pings()
        self.assertEqual(len(pings), 0)
    
    async def test_confirm_invitation_no_session(self):
        """Test confirmation with no session"""
        # Remove session
        self.storage.remove_user_session(12345)
        
        result = await self.handler.confirm_invitation(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_confirm_invitation_invalid_action(self):
        """Test confirmation with invalid action"""
        self.mock_callback.data = "confirm_invalid"
        
        result = await self.handler.confirm_invitation(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_confirm_invitation_edit_message_fallback(self):
        """Test confirmation with edit message failure"""
        # Make edit_text fail
        self.mock_callback.message.edit_text.side_effect = Exception("Edit failed")
        
        result = await self.handler.confirm_invitation(self.mock_update, self.mock_context)
        
        # Should still succeed with fallback
        self.assertEqual(result, ConversationHandler.END)
        
        # Should try edit first, then fallback to reply
        self.mock_callback.message.edit_text.assert_called_once()
        self.mock_callback.message.reply_text.assert_called_once()
        
        # Should still create ping record
        pings = self.storage.get_recent_pings()
        self.assertEqual(len(pings), 1)
    
    async def test_send_invitations_with_flexible_time(self):
        """Test sending invitations with flexible time"""
        # Set flexible time
        session = self.storage.get_user_session(12345)
        session.set_time("")  # Flexible time
        self.storage.update_user_session(session)
        
        result = await self.handler.confirm_invitation(self.mock_update, self.mock_context)
        
        # Should succeed
        self.assertEqual(result, ConversationHandler.END)
        
        # Should create ping with empty time
        pings = self.storage.get_recent_pings()
        self.assertEqual(len(pings), 1)
        self.assertEqual(pings[0].time, "")
    
    async def test_send_invitations_many_friends(self):
        """Test sending invitations with many friends"""
        # Add more friends
        session = self.storage.get_user_session(12345)
        for i in range(2, min(6, len(FRIENDS))):  # Add up to 4 more friends
            session.toggle_friend(FRIENDS[i])
        self.storage.update_user_session(session)
        
        result = await self.handler.confirm_invitation(self.mock_update, self.mock_context)
        
        # Should succeed
        self.assertEqual(result, ConversationHandler.END)
        
        # Should create ping with all friends
        pings = self.storage.get_recent_pings()
        self.assertEqual(len(pings), 1)
        
        # Should show truncated notification preview
        sent_message = self.mock_callback.message.edit_text.call_args[0][0]
        if len(session.selected_friends) > 3:
            self.assertIn("and", sent_message)
            self.assertIn("more", sent_message)
    
    def test_create_notification_preview(self):
        """Test notification preview creation"""
        ping = PingRecord(
            organizer_id=12345,
            organizer_name="testuser",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=[FRIENDS[0], FRIENDS[1], FRIENDS[2], FRIENDS[3]]
        )
        
        # Test with default limit (3)
        preview = self.handler.create_notification_preview(ping)
        
        self.assertIn(FRIENDS[0], preview)
        self.assertIn(FRIENDS[1], preview)
        self.assertIn(FRIENDS[2], preview)
        self.assertNotIn(FRIENDS[3], preview)  # Should be truncated
        self.assertIn("and 1 more friend", preview)
        
        # Test with custom limit
        preview = self.handler.create_notification_preview(ping, max_friends=2)
        
        self.assertIn(FRIENDS[0], preview)
        self.assertIn(FRIENDS[1], preview)
        self.assertNotIn(FRIENDS[2], preview)
        self.assertIn("and 2 more friends", preview)
    
    def test_create_notification_preview_few_friends(self):
        """Test notification preview with few friends"""
        ping = PingRecord(
            organizer_id=12345,
            organizer_name="testuser",
            meetup_type="lunch",
            location="Campus Café",
            time="12:30 PM",
            invited_friends=[FRIENDS[0], FRIENDS[1]]
        )
        
        preview = self.handler.create_notification_preview(ping)
        
        self.assertIn(FRIENDS[0], preview)
        self.assertIn(FRIENDS[1], preview)
        self.assertNotIn("more", preview)  # No truncation needed


class TestStandaloneConfirmation(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.storage = StorageManager()
        
        # Mock update and context
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_context.bot_data = {'storage_manager': self.storage}
        
        # Mock user and callback
        self.mock_user = Mock()
        self.mock_user.id = 12345
        self.mock_user.username = "testuser"
        
        self.mock_callback = Mock()
        self.mock_callback.data = "confirm_send"
        self.mock_callback.answer = AsyncMock()
        self.mock_callback.message = Mock()
        self.mock_callback.message.edit_text = AsyncMock()
        
        self.mock_update.effective_user = self.mock_user
        self.mock_update.callback_query = self.mock_callback
        
        # Create complete session
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        session.set_time("12:30 PM")
        session.toggle_friend(FRIENDS[0])
        session.current_state = ConversationState.CONFIRM
        self.storage.update_user_session(session)
    
    async def test_standalone_confirm_invitation(self):
        """Test standalone confirmation function"""
        result = await confirm_invitation(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
        
        # Should create ping record
        pings = self.storage.get_recent_pings()
        self.assertEqual(len(pings), 1)
    
    async def test_standalone_confirm_invitation_no_storage(self):
        """Test standalone confirmation with no storage"""
        self.mock_context.bot_data = {}
        
        result = await confirm_invitation(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)


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
for cls in [TestInvitationConfirmation, TestStandaloneConfirmation]:
    for method_name in dir(cls):
        if method_name.startswith('test_') and 'async' in method_name:
            method = getattr(cls, method_name)
            if asyncio.iscoroutinefunction(method):
                setattr(cls, method_name, 
                       lambda self, m=method: run_async_test(m(self)))


if __name__ == "__main__":
    unittest.main()