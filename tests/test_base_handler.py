"""
Unit tests for BaseHandler
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from handlers.base import BaseHandler
from storage.manager import StorageManager
from models.user_session import UserSession


class TestBaseHandler(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.storage = StorageManager()
        self.handler = BaseHandler(self.storage)
        
        # Mock update and context objects
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
        
        # Set up update object
        self.mock_update.effective_user = self.mock_user
        self.mock_update.effective_chat = self.mock_chat
        self.mock_update.message = self.mock_message
        self.mock_update.callback_query = None
    
    def test_handler_initialization(self):
        """Test BaseHandler initialization"""
        self.assertEqual(self.handler.storage, self.storage)
        self.assertIsNotNone(self.handler.logger)
    
    def test_get_user_id(self):
        """Test extracting user ID from update"""
        user_id = self.handler._get_user_id(self.mock_update)
        self.assertEqual(user_id, 12345)
        
        # Test with no user
        self.mock_update.effective_user = None
        user_id = self.handler._get_user_id(self.mock_update)
        self.assertIsNone(user_id)
    
    def test_get_username(self):
        """Test extracting username from update"""
        username = self.handler._get_username(self.mock_update)
        self.assertEqual(username, "testuser")
        
        # Test with no username but first name
        self.mock_user.username = None
        username = self.handler._get_username(self.mock_update)
        self.assertEqual(username, "Test")
        
        # Test with no user
        self.mock_update.effective_user = None
        username = self.handler._get_username(self.mock_update)
        self.assertIsNone(username)
    
    def test_get_chat_id(self):
        """Test extracting chat ID from update"""
        chat_id = self.handler._get_chat_id(self.mock_update)
        self.assertEqual(chat_id, 67890)
        
        # Test with no chat
        self.mock_update.effective_chat = None
        chat_id = self.handler._get_chat_id(self.mock_update)
        self.assertIsNone(chat_id)
    
    async def test_safe_reply_with_message(self):
        """Test safe reply with message update"""
        result = await self.handler._safe_reply(self.mock_update, "Test message")
        
        self.assertTrue(result)
        self.mock_message.reply_text.assert_called_once_with("Test message")
    
    async def test_safe_reply_with_callback(self):
        """Test safe reply with callback query update"""
        self.mock_update.message = None
        self.mock_update.callback_query = self.mock_callback
        
        result = await self.handler._safe_reply(self.mock_update, "Test message")
        
        self.assertTrue(result)
        self.mock_callback.message.reply_text.assert_called_once_with("Test message")
    
    async def test_safe_reply_no_message_or_callback(self):
        """Test safe reply with no message or callback"""
        self.mock_update.message = None
        self.mock_update.callback_query = None
        
        result = await self.handler._safe_reply(self.mock_update, "Test message")
        
        self.assertFalse(result)
    
    async def test_safe_reply_exception(self):
        """Test safe reply with exception"""
        self.mock_message.reply_text.side_effect = Exception("Send failed")
        
        result = await self.handler._safe_reply(self.mock_update, "Test message")
        
        self.assertFalse(result)
    
    async def test_safe_edit_message(self):
        """Test safe message editing"""
        self.mock_update.callback_query = self.mock_callback
        self.mock_callback.message.edit_text = AsyncMock()
        
        result = await self.handler._safe_edit_message(self.mock_update, "Edited message")
        
        self.assertTrue(result)
        self.mock_callback.message.edit_text.assert_called_once_with("Edited message")
    
    async def test_safe_edit_message_no_callback(self):
        """Test safe message editing with no callback"""
        self.mock_update.callback_query = None
        
        result = await self.handler._safe_edit_message(self.mock_update, "Edited message")
        
        self.assertFalse(result)
    
    async def test_safe_answer_callback(self):
        """Test safe callback answering"""
        self.mock_update.callback_query = self.mock_callback
        
        result = await self.handler._safe_answer_callback(self.mock_update, "Callback text")
        
        self.assertTrue(result)
        self.mock_callback.answer.assert_called_once_with("Callback text")
    
    async def test_safe_answer_callback_no_callback(self):
        """Test safe callback answering with no callback"""
        self.mock_update.callback_query = None
        
        result = await self.handler._safe_answer_callback(self.mock_update)
        
        self.assertFalse(result)
    
    def test_validate_user_input(self):
        """Test user input validation"""
        # Valid input
        self.assertTrue(self.handler._validate_user_input("Valid text"))
        
        # Empty string
        self.assertFalse(self.handler._validate_user_input(""))
        
        # Whitespace only
        self.assertFalse(self.handler._validate_user_input("   "))
        
        # None input
        self.assertFalse(self.handler._validate_user_input(None))
        
        # Non-string input
        self.assertFalse(self.handler._validate_user_input(123))
        
        # Too long input
        long_text = "x" * 101
        self.assertFalse(self.handler._validate_user_input(long_text, max_length=100))
        
        # Just at limit
        limit_text = "x" * 100
        self.assertTrue(self.handler._validate_user_input(limit_text, max_length=100))
    
    def test_log_user_action(self):
        """Test user action logging"""
        with patch.object(self.handler.logger, 'info') as mock_log:
            self.handler._log_user_action(12345, "test_action")
            mock_log.assert_called_once()
            
            # Check log message contains user ID and action
            log_call = mock_log.call_args[0][0]
            self.assertIn("12345", log_call)
            self.assertIn("test_action", log_call)
    
    def test_log_user_action_with_details(self):
        """Test user action logging with details"""
        with patch.object(self.handler.logger, 'info') as mock_log:
            self.handler._log_user_action(12345, "test_action", "extra details")
            
            log_call = mock_log.call_args[0][0]
            self.assertIn("extra details", log_call)
    
    async def test_cleanup_user_session(self):
        """Test user session cleanup"""
        # Create a session with some data
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        
        # Cleanup session
        await self.handler._cleanup_user_session(12345, "test cleanup")
        
        # Verify session was reset
        updated_session = self.storage.get_user_session(12345)
        self.assertIsNone(updated_session.meetup_type)
        self.assertIsNone(updated_session.location)
    
    def test_is_valid_callback_data(self):
        """Test callback data validation"""
        # Valid callback data
        self.assertTrue(self.handler._is_valid_callback_data("valid_callback"))
        
        # Invalid callback data
        self.assertFalse(self.handler._is_valid_callback_data(None))
        self.assertFalse(self.handler._is_valid_callback_data(""))
        self.assertFalse(self.handler._is_valid_callback_data(123))
        
        # With expected prefix
        self.assertTrue(self.handler._is_valid_callback_data("loc_0", "loc_"))
        self.assertFalse(self.handler._is_valid_callback_data("friend_0", "loc_"))
    
    async def test_send_typing_action(self):
        """Test sending typing action"""
        self.mock_context.bot = Mock()
        self.mock_context.bot.send_chat_action = AsyncMock()
        
        result = await self.handler._send_typing_action(self.mock_update, self.mock_context)
        
        self.assertTrue(result)
        self.mock_context.bot.send_chat_action.assert_called_once_with(
            chat_id=67890, action="typing"
        )
    
    async def test_send_typing_action_no_chat(self):
        """Test sending typing action with no chat ID"""
        self.mock_update.effective_chat = None
        
        result = await self.handler._send_typing_action(self.mock_update, self.mock_context)
        
        self.assertFalse(result)
    
    def test_get_storage_manager(self):
        """Test getting storage manager"""
        storage = self.handler.get_storage_manager()
        self.assertEqual(storage, self.storage)
    
    async def test_handle_error(self):
        """Test error handling"""
        test_error = Exception("Test error")
        
        with patch.object(self.handler.logger, 'error') as mock_log:
            await self.handler.handle_error(
                self.mock_update, self.mock_context, test_error, "Custom error"
            )
            
            # Should log the error
            mock_log.assert_called_once()
            
            # Should send error message to user
            self.mock_message.reply_text.assert_called_once()
            
            # Check that error message contains custom message
            sent_message = self.mock_message.reply_text.call_args[0][0]
            self.assertIn("Custom error", sent_message)
    
    async def test_handle_error_with_callback(self):
        """Test error handling with callback query"""
        self.mock_update.message = None
        self.mock_update.callback_query = self.mock_callback
        
        test_error = Exception("Test error")
        
        await self.handler.handle_error(self.mock_update, self.mock_context, test_error)
        
        # Should send error message via callback message
        self.mock_callback.message.reply_text.assert_called_once()
        # Should answer the callback
        self.mock_callback.answer.assert_called_once()


# Helper function to run async tests
def run_async_test(coro):
    """Helper to run async test methods"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Patch test methods to run async tests
for method_name in dir(TestBaseHandler):
    if method_name.startswith('test_') and 'async' in method_name:
        method = getattr(TestBaseHandler, method_name)
        if asyncio.iscoroutinefunction(method):
            setattr(TestBaseHandler, method_name, 
                   lambda self, m=method: run_async_test(m(self)))


if __name__ == "__main__":
    unittest.main()