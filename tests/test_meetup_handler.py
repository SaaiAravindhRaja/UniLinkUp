"""
Unit tests for MeetupHandler
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from telegram.ext import ConversationHandler

from handlers.meetup import MeetupHandler, lunch_command, study_command, cancel_command
from storage.manager import StorageManager
from config.constants import ConversationState


class TestMeetupHandler(unittest.TestCase):
    
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
        self.mock_user.first_name = "Test"
        
        # Mock chat
        self.mock_chat = Mock()
        self.mock_chat.id = 67890
        
        # Mock message
        self.mock_message = Mock()
        self.mock_message.reply_text = AsyncMock()
        
        # Mock callback query
        self.mock_callback = Mock()
        self.mock_callback.answer = AsyncMock()
        self.mock_callback.message = self.mock_message
        
        # Set up update
        self.mock_update.effective_user = self.mock_user
        self.mock_update.effective_chat = self.mock_chat
        self.mock_update.message = self.mock_message
        self.mock_update.callback_query = None
        
        # Mock bot for typing action
        self.mock_context.bot = Mock()
        self.mock_context.bot.send_chat_action = AsyncMock()
    
    def test_handler_initialization(self):
        """Test MeetupHandler initialization"""
        self.assertEqual(self.handler.storage, self.storage)
        self.assertIsNotNone(self.handler.keyboard_factory)
        self.assertIsNotNone(self.handler.logger)
    
    async def test_lunch_command_success(self):
        """Test successful lunch command"""
        result = await self.handler.lunch_command(self.mock_update, self.mock_context)
        
        # Should return LOCATION state
        self.assertEqual(result, ConversationState.LOCATION.value)
        
        # Should send message with keyboard
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args
        
        # Check message content
        message_text = call_args[0][0]
        self.assertIn("lunch", message_text.lower())
        
        # Check keyboard was provided
        self.assertIn("reply_markup", call_args[1])
        
        # Check session was created and configured
        session = self.storage.get_user_session(12345)
        self.assertEqual(session.meetup_type, "lunch")
        self.assertEqual(session.current_state, ConversationState.LOCATION)
    
    async def test_study_command_success(self):
        """Test successful study command"""
        result = await self.handler.study_command(self.mock_update, self.mock_context)
        
        # Should return LOCATION state
        self.assertEqual(result, ConversationState.LOCATION.value)
        
        # Should send message with keyboard
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args
        
        # Check message content
        message_text = call_args[0][0]
        self.assertIn("study", message_text.lower())
        
        # Check session was created and configured
        session = self.storage.get_user_session(12345)
        self.assertEqual(session.meetup_type, "study")
        self.assertEqual(session.current_state, ConversationState.LOCATION)
    
    async def test_meetup_command_no_user_id(self):
        """Test meetup command with no user ID"""
        self.mock_update.effective_user = None
        
        result = await self.handler.lunch_command(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_meetup_command_reply_failure(self):
        """Test meetup command with reply failure"""
        self.mock_message.reply_text.side_effect = Exception("Send failed")
        
        result = await self.handler.lunch_command(self.mock_update, self.mock_context)
        
        # Should end conversation on failure
        self.assertEqual(result, ConversationHandler.END)
        
        # Session should be cleaned up
        session = self.storage.get_user_session(12345)
        self.assertIsNone(session.meetup_type)
    
    async def test_meetup_command_resets_existing_session(self):
        """Test that meetup command resets existing session data"""
        # Create session with existing data
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("study")
        session.set_location("Library")
        session.toggle_friend("Alice")
        
        # Start new lunch command
        result = await self.handler.lunch_command(self.mock_update, self.mock_context)
        
        self.assertEqual(result, ConversationState.LOCATION.value)
        
        # Session should be reset with new meetup type
        updated_session = self.storage.get_user_session(12345)
        self.assertEqual(updated_session.meetup_type, "lunch")
        self.assertIsNone(updated_session.location)
        self.assertEqual(len(updated_session.selected_friends), 0)
    
    async def test_cancel_conversation(self):
        """Test conversation cancellation"""
        # Set up session with some data
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        
        result = await self.handler.cancel_conversation(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
        
        # Should send cancellation message
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("cancelled", sent_message.lower())
        
        # Session should be cleaned up
        updated_session = self.storage.get_user_session(12345)
        self.assertIsNone(updated_session.meetup_type)
        self.assertIsNone(updated_session.location)
    
    async def test_cancel_conversation_with_callback(self):
        """Test conversation cancellation with callback query"""
        self.mock_update.callback_query = self.mock_callback
        
        result = await self.handler.cancel_conversation(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
        
        # Should answer callback
        self.mock_callback.answer.assert_called_once()
    
    async def test_timeout_conversation(self):
        """Test conversation timeout handling"""
        # Set up session
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        
        result = await self.handler.timeout_conversation(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
        
        # Should send timeout message
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("timed out", sent_message.lower())
        
        # Session should be cleaned up
        updated_session = self.storage.get_user_session(12345)
        self.assertIsNone(updated_session.meetup_type)
    
    def test_get_conversation_state_value(self):
        """Test conversation state value mapping"""
        self.assertEqual(self.handler.get_conversation_state_value(ConversationState.LOCATION), 1)
        self.assertEqual(self.handler.get_conversation_state_value(ConversationState.TIME), 2)
        self.assertEqual(self.handler.get_conversation_state_value(ConversationState.FRIENDS), 3)
        self.assertEqual(self.handler.get_conversation_state_value(ConversationState.CONFIRM), 4)
    
    def test_get_user_session_safely(self):
        """Test safe user session retrieval"""
        # Create session
        self.storage.get_user_session(12345, "testuser")
        
        # Should return session
        session = self.handler.get_user_session_safely(12345)
        self.assertIsNotNone(session)
        self.assertEqual(session.user_id, 12345)
        
        # Test with storage error
        with patch.object(self.storage, 'get_user_session', side_effect=Exception("Storage error")):
            session = self.handler.get_user_session_safely(12345)
            self.assertIsNone(session)
    
    async def test_handle_invalid_state(self):
        """Test invalid state handling"""
        result = await self.handler.handle_invalid_state(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
        
        # Should send error message
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("went wrong", sent_message)
        self.assertIn("start over", sent_message)
    
    async def test_handle_invalid_state_with_callback(self):
        """Test invalid state handling with callback query"""
        self.mock_update.callback_query = self.mock_callback
        
        result = await self.handler.handle_invalid_state(self.mock_update, self.mock_context)
        
        # Should answer callback
        self.mock_callback.answer.assert_called_once()
    
    def test_validate_meetup_session(self):
        """Test meetup session validation"""
        # Valid session
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        
        is_valid, error = self.handler.validate_meetup_session(session)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
        
        # No session
        is_valid, error = self.handler.validate_meetup_session(None)
        self.assertFalse(is_valid)
        self.assertIn("No session", error)
        
        # No meetup type
        session.meetup_type = None
        is_valid, error = self.handler.validate_meetup_session(session)
        self.assertFalse(is_valid)
        self.assertIn("No meetup type", error)
        
        # Invalid meetup type
        session.meetup_type = "invalid"
        is_valid, error = self.handler.validate_meetup_session(session)
        self.assertFalse(is_valid)
        self.assertIn("Invalid meetup type", error)
    
    async def test_send_state_debug_info(self):
        """Test sending debug information"""
        # Create session with data
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        
        await self.handler.send_state_debug_info(self.mock_update, 12345)
        
        # Should send debug message
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("Debug Info", sent_message)
        self.assertIn("testuser", sent_message)
        self.assertIn("lunch", sent_message)
    
    async def test_send_state_debug_info_no_session(self):
        """Test sending debug info with no session"""
        await self.handler.send_state_debug_info(self.mock_update, 99999)
        
        # Should send no session message
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("No session found", sent_message)


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
    
    async def test_standalone_lunch_command(self):
        """Test standalone lunch command function"""
        result = await lunch_command(self.mock_update, self.mock_context)
        
        # Should return location state
        self.assertEqual(result, ConversationState.LOCATION.value)
        
        # Should create session
        session = self.storage.get_user_session(12345)
        self.assertEqual(session.meetup_type, "lunch")
    
    async def test_standalone_study_command(self):
        """Test standalone study command function"""
        result = await study_command(self.mock_update, self.mock_context)
        
        # Should return location state
        self.assertEqual(result, ConversationState.LOCATION.value)
        
        # Should create session
        session = self.storage.get_user_session(12345)
        self.assertEqual(session.meetup_type, "study")
    
    async def test_standalone_cancel_command(self):
        """Test standalone cancel command function"""
        result = await cancel_command(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_standalone_commands_no_storage(self):
        """Test standalone commands with no storage manager"""
        self.mock_context.bot_data = {}
        
        # Test lunch command
        result = await lunch_command(self.mock_update, self.mock_context)
        self.assertEqual(result, ConversationHandler.END)
        
        # Should send error message
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
for cls in [TestMeetupHandler, TestStandaloneFunctions]:
    for method_name in dir(cls):
        if method_name.startswith('test_') and 'async' in method_name:
            method = getattr(cls, method_name)
            if asyncio.iscoroutinefunction(method):
                setattr(cls, method_name, 
                       lambda self, m=method: run_async_test(m(self)))


if __name__ == "__main__":
    unittest.main()