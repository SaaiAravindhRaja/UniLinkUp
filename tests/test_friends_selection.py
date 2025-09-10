"""
Unit tests for friends selection handling
"""

import unittest
from unittest.mock import Mock, AsyncMock
import asyncio
from telegram.ext import ConversationHandler

from handlers.meetup import MeetupHandler, friends_callback
from storage.manager import StorageManager
from config.constants import ConversationState, FRIENDS


class TestFriendsSelection(unittest.TestCase):
    
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
        self.mock_callback.data = "friend_0"
        self.mock_callback.answer = AsyncMock()
        self.mock_callback.message = Mock()
        self.mock_callback.message.edit_text = AsyncMock()
        self.mock_callback.message.reply_text = AsyncMock()
        
        # Set up update
        self.mock_update.effective_user = self.mock_user
        self.mock_update.callback_query = self.mock_callback
        
        # Create session with time set
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        session.set_time("12:30 PM")
        session.current_state = ConversationState.FRIENDS
        self.storage.update_user_session(session)
    
    async def test_friend_toggle_add(self):
        """Test adding a friend to selection"""
        result = await self.handler.friends_callback(self.mock_update, self.mock_context)
        
        # Should stay in FRIENDS state
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Should add friend to session
        session = self.storage.get_user_session(12345)
        self.assertIn(FRIENDS[0], session.selected_friends)
        
        # Should edit message
        self.mock_callback.message.edit_text.assert_called_once()
        
        # Should answer callback
        self.mock_callback.answer.assert_called_once()
        callback_text = self.mock_callback.answer.call_args[0][0]
        self.assertIn("Added", callback_text)
        self.assertIn(FRIENDS[0], callback_text)
    
    async def test_friend_toggle_remove(self):
        """Test removing a friend from selection"""
        # First add the friend
        session = self.storage.get_user_session(12345)
        session.toggle_friend(FRIENDS[0])
        self.storage.update_user_session(session)
        
        # Now toggle again to remove
        result = await self.handler.friends_callback(self.mock_update, self.mock_context)
        
        # Should stay in FRIENDS state
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Should remove friend from session
        updated_session = self.storage.get_user_session(12345)
        self.assertNotIn(FRIENDS[0], updated_session.selected_friends)
        
        # Should answer callback with removal message
        callback_text = self.mock_callback.answer.call_args[0][0]
        self.assertIn("Removed", callback_text)
    
    async def test_friend_toggle_multiple_friends(self):
        """Test selecting multiple friends"""
        # Select first friend
        result = await self.handler.friends_callback(self.mock_update, self.mock_context)
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Select second friend
        self.mock_callback.data = "friend_1"
        self.mock_callback.message.edit_text.reset_mock()
        self.mock_callback.answer.reset_mock()
        
        result = await self.handler.friends_callback(self.mock_update, self.mock_context)
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Should have both friends selected
        session = self.storage.get_user_session(12345)
        self.assertIn(FRIENDS[0], session.selected_friends)
        self.assertIn(FRIENDS[1], session.selected_friends)
        self.assertEqual(len(session.selected_friends), 2)
    
    async def test_friend_toggle_invalid_index(self):
        """Test friend toggle with invalid index"""
        self.mock_callback.data = "friend_999"
        
        result = await self.handler.friends_callback(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_friend_toggle_invalid_format(self):
        """Test friend toggle with invalid callback format"""
        self.mock_callback.data = "friend_abc"
        
        result = await self.handler.friends_callback(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_friends_confirmation_yes_with_friends(self):
        """Test confirming friends selection with friends selected"""
        # First select a friend
        session = self.storage.get_user_session(12345)
        session.toggle_friend(FRIENDS[0])
        self.storage.update_user_session(session)
        
        # Now confirm
        self.mock_callback.data = "confirm_yes"
        
        result = await self.handler.friends_callback(self.mock_update, self.mock_context)
        
        # Should move to CONFIRM state
        self.assertEqual(result, ConversationState.CONFIRM.value)
        
        # Should update session state
        updated_session = self.storage.get_user_session(12345)
        self.assertEqual(updated_session.current_state, ConversationState.CONFIRM)
        
        # Should edit message with confirmation
        self.mock_callback.message.edit_text.assert_called_once()
    
    async def test_friends_confirmation_yes_no_friends(self):
        """Test confirming friends selection with no friends selected"""
        self.mock_callback.data = "confirm_yes"
        
        result = await self.handler.friends_callback(self.mock_update, self.mock_context)
        
        # Should stay in FRIENDS state
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Should send error message
        self.mock_callback.message.reply_text.assert_called_once()
        sent_message = self.mock_callback.message.reply_text.call_args[0][0]
        self.assertIn("select at least one friend", sent_message)
    
    async def test_friends_confirmation_cancel(self):
        """Test cancelling friends selection"""
        self.mock_callback.data = "confirm_cancel"
        
        result = await self.handler.friends_callback(self.mock_update, self.mock_context)
        
        # Should end conversation (cancel)
        self.assertEqual(result, ConversationHandler.END)
        
        # Should send cancellation message
        self.mock_callback.message.reply_text.assert_called_once()
        sent_message = self.mock_callback.message.reply_text.call_args[0][0]
        self.assertIn("cancelled", sent_message.lower())
    
    async def test_friends_callback_no_session(self):
        """Test friends callback with no session"""
        # Remove session
        self.storage.remove_user_session(12345)
        
        result = await self.handler.friends_callback(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_friends_callback_edit_message_fallback(self):
        """Test friends callback with edit message failure"""
        # Make edit_text fail
        self.mock_callback.message.edit_text.side_effect = Exception("Edit failed")
        
        result = await self.handler.friends_callback(self.mock_update, self.mock_context)
        
        # Should still succeed with fallback
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Should try edit first, then fallback to reply
        self.mock_callback.message.edit_text.assert_called_once()
        self.mock_callback.message.reply_text.assert_called_once()
    
    async def test_friends_callback_invalid_action(self):
        """Test friends callback with invalid action"""
        self.mock_callback.data = "invalid_action"
        
        result = await self.handler.friends_callback(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_handle_friend_toggle_method(self):
        """Test _handle_friend_toggle method directly"""
        session = self.storage.get_user_session(12345)
        
        result = await self.handler._handle_friend_toggle(
            self.mock_update, self.mock_context, session, "0"
        )
        
        # Should stay in FRIENDS state
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Should add friend
        self.assertIn(FRIENDS[0], session.selected_friends)
    
    async def test_handle_friends_confirmation_method(self):
        """Test _handle_friends_confirmation method directly"""
        session = self.storage.get_user_session(12345)
        session.toggle_friend(FRIENDS[0])  # Add a friend first
        
        result = await self.handler._handle_friends_confirmation(
            self.mock_update, self.mock_context, session, "yes"
        )
        
        # Should move to CONFIRM state
        self.assertEqual(result, ConversationState.CONFIRM.value)
        self.assertEqual(session.current_state, ConversationState.CONFIRM)


class TestStandaloneFriendsCallback(unittest.TestCase):
    
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
        self.mock_callback.data = "friend_0"
        self.mock_callback.answer = AsyncMock()
        self.mock_callback.message = Mock()
        self.mock_callback.message.edit_text = AsyncMock()
        
        self.mock_update.effective_user = self.mock_user
        self.mock_update.callback_query = self.mock_callback
        
        # Create session
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        session.current_state = ConversationState.FRIENDS
        self.storage.update_user_session(session)
    
    async def test_standalone_friends_callback(self):
        """Test standalone friends callback function"""
        result = await friends_callback(self.mock_update, self.mock_context)
        
        # Should stay in FRIENDS state
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Should update session
        session = self.storage.get_user_session(12345)
        self.assertIn(FRIENDS[0], session.selected_friends)
    
    async def test_standalone_friends_callback_no_storage(self):
        """Test standalone friends callback with no storage"""
        self.mock_context.bot_data = {}
        
        result = await friends_callback(self.mock_update, self.mock_context)
        
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
for cls in [TestFriendsSelection, TestStandaloneFriendsCallback]:
    for method_name in dir(cls):
        if method_name.startswith('test_') and 'async' in method_name:
            method = getattr(cls, method_name)
            if asyncio.iscoroutinefunction(method):
                setattr(cls, method_name, 
                       lambda self, m=method: run_async_test(m(self)))


if __name__ == "__main__":
    unittest.main()