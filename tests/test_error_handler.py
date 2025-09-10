"""
Unit tests for ErrorHandler
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from telegram.error import NetworkError, TimedOut, BadRequest, TelegramError

from handlers.error import ErrorHandler, get_error_handler, global_error_handler
from storage.manager import StorageManager


class TestErrorHandler(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.storage = StorageManager()
        self.error_handler = ErrorHandler(self.storage)
        
        # Mock update and context
        self.mock_update = Mock()
        self.mock_context = Mock()
        
        # Mock user and chat
        self.mock_user = Mock()
        self.mock_user.id = 12345
        
        self.mock_chat = Mock()
        self.mock_chat.id = 67890
        
        self.mock_update.effective_user = self.mock_user
        self.mock_update.effective_chat = self.mock_chat
        self.mock_update.message = None
        self.mock_update.callback_query = None
        
        # Mock bot
        self.mock_context.bot = Mock()
        self.mock_context.bot.send_message = AsyncMock()
    
    def test_error_handler_initialization(self):
        """Test ErrorHandler initialization"""
        handler = ErrorHandler()
        self.assertIsNone(handler.storage_manager)
        self.assertEqual(handler.error_count, 0)
        self.assertEqual(len(handler.last_errors), 0)
        
        # With storage manager
        handler_with_storage = ErrorHandler(self.storage)
        self.assertEqual(handler_with_storage.storage_manager, self.storage)
    
    def test_store_error_info(self):
        """Test error information storage"""
        error = ValueError("Test error")
        
        self.error_handler._store_error_info(error, self.mock_update)
        
        # Should store error info
        self.assertEqual(len(self.error_handler.last_errors), 1)
        
        error_info = self.error_handler.last_errors[0]
        self.assertEqual(error_info["error_type"], "ValueError")
        self.assertEqual(error_info["error_message"], "Test error")
        self.assertEqual(error_info["user_id"], 12345)
        self.assertEqual(error_info["chat_id"], 67890)
    
    def test_store_error_info_with_message(self):
        """Test error storage with message data"""
        # Add message to update
        mock_message = Mock()
        mock_message.text = "test message"
        self.mock_update.message = mock_message
        
        error = RuntimeError("Test error")
        self.error_handler._store_error_info(error, self.mock_update)
        
        error_info = self.error_handler.last_errors[0]
        self.assertEqual(error_info["message_text"], "test message")
    
    def test_store_error_info_with_callback(self):
        """Test error storage with callback data"""
        # Add callback query to update
        mock_callback = Mock()
        mock_callback.data = "test_callback"
        self.mock_update.callback_query = mock_callback
        
        error = RuntimeError("Test error")
        self.error_handler._store_error_info(error, self.mock_update)
        
        error_info = self.error_handler.last_errors[0]
        self.assertEqual(error_info["callback_data"], "test_callback")
    
    def test_error_history_limit(self):
        """Test error history limit enforcement"""
        # Add more errors than the limit
        for i in range(15):
            error = ValueError(f"Error {i}")
            self.error_handler._store_error_info(error, self.mock_update)
        
        # Should keep only the maximum number
        self.assertEqual(len(self.error_handler.last_errors), 10)
        
        # Should keep the most recent ones
        last_error = self.error_handler.last_errors[-1]
        self.assertEqual(last_error["error_message"], "Error 14")
    
    async def test_handle_network_error(self):
        """Test network error handling"""
        error = NetworkError("Network failed")
        self.mock_context.error = error
        
        await self.error_handler._handle_network_error(self.mock_update, self.mock_context, error)
        
        # Should not try to send message for network errors
        self.mock_context.bot.send_message.assert_not_called()
    
    async def test_handle_timeout_error(self):
        """Test timeout error handling"""
        error = TimedOut("Request timed out")
        self.mock_context.error = error
        
        await self.error_handler._handle_timeout_error(self.mock_update, self.mock_context, error)
        
        # Should try to send timeout message
        self.mock_context.bot.send_message.assert_called_once()
        call_args = self.mock_context.bot.send_message.call_args
        self.assertEqual(call_args[1]["chat_id"], 67890)
        self.assertIn("timed out", call_args[1]["text"])
    
    async def test_handle_bad_request_error(self):
        """Test bad request error handling"""
        error = BadRequest("Invalid request")
        self.mock_context.error = error
        
        await self.error_handler._handle_bad_request_error(self.mock_update, self.mock_context, error)
        
        # Should send error message
        self.mock_context.bot.send_message.assert_called_once()
        call_args = self.mock_context.bot.send_message.call_args
        self.assertIn("Invalid request", call_args[1]["text"])
    
    async def test_handle_telegram_error(self):
        """Test general Telegram error handling"""
        error = TelegramError("API error")
        self.mock_context.error = error
        
        await self.error_handler._handle_telegram_error(self.mock_update, self.mock_context, error)
        
        # Should send error message
        self.mock_context.bot.send_message.assert_called_once()
        call_args = self.mock_context.bot.send_message.call_args
        self.assertIn("Telegram service error", call_args[1]["text"])
    
    async def test_handle_general_error(self):
        """Test general error handling"""
        error = Exception("General error")
        self.mock_context.error = error
        
        await self.error_handler._handle_general_error(self.mock_update, self.mock_context, error)
        
        # Should send error message
        self.mock_context.bot.send_message.assert_called_once()
    
    async def test_cleanup_after_error(self):
        """Test cleanup after error"""
        # Create a session with some state
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        self.storage.update_user_session(session)
        
        error = Exception("Test error")
        
        await self.error_handler._cleanup_after_error(self.mock_update, self.mock_context, error)
        
        # Should reset session
        updated_session = self.storage.get_user_session(12345)
        self.assertIsNone(updated_session.meetup_type)
        self.assertIsNone(updated_session.location)
    
    async def test_cleanup_with_callback_query(self):
        """Test cleanup with pending callback query"""
        # Add callback query
        mock_callback = Mock()
        mock_callback.answer = AsyncMock()
        self.mock_update.callback_query = mock_callback
        
        error = Exception("Test error")
        
        await self.error_handler._cleanup_after_error(self.mock_update, self.mock_context, error)
        
        # Should answer callback query
        mock_callback.answer.assert_called_once()
    
    def test_get_error_statistics(self):
        """Test error statistics"""
        # Add some errors
        errors = [
            ValueError("Error 1"),
            ValueError("Error 2"),
            RuntimeError("Error 3"),
            TypeError("Error 4")
        ]
        
        for error in errors:
            self.error_handler._store_error_info(error, self.mock_update)
        
        self.error_handler.error_count = 10  # Simulate more total errors
        
        stats = self.error_handler.get_error_statistics()
        
        self.assertEqual(stats["total_errors"], 10)
        self.assertEqual(stats["recent_errors"], 4)
        self.assertEqual(stats["error_types"]["ValueError"], 2)
        self.assertEqual(stats["error_types"]["RuntimeError"], 1)
        self.assertEqual(stats["error_types"]["TypeError"], 1)
        self.assertIsNotNone(stats["last_error"])
    
    def test_reset_error_count(self):
        """Test error count reset"""
        # Add some errors
        self.error_handler.error_count = 5
        self.error_handler._store_error_info(ValueError("Test"), self.mock_update)
        
        previous_count = self.error_handler.reset_error_count()
        
        self.assertEqual(previous_count, 5)
        self.assertEqual(self.error_handler.error_count, 0)
        self.assertEqual(len(self.error_handler.last_errors), 0)


class TestGlobalErrorHandler(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Reset global error handler
        import handlers.error
        handlers.error._global_error_handler = None
    
    def test_get_error_handler_singleton(self):
        """Test error handler singleton pattern"""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        # Should return same instance
        self.assertIs(handler1, handler2)
    
    def test_get_error_handler_with_storage(self):
        """Test error handler with storage manager"""
        storage = StorageManager()
        
        handler = get_error_handler(storage)
        self.assertEqual(handler.storage_manager, storage)
        
        # Second call should update storage if not set
        handler2 = get_error_handler()
        self.assertEqual(handler2.storage_manager, storage)
    
    async def test_global_error_handler_function(self):
        """Test global error handler function"""
        mock_update = Mock()
        mock_context = Mock()
        mock_context.error = ValueError("Test error")
        
        # Should not raise exception
        await global_error_handler(mock_update, mock_context)


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
for cls in [TestErrorHandler, TestGlobalErrorHandler]:
    for method_name in dir(cls):
        if method_name.startswith('test_') and 'async' in method_name:
            method = getattr(cls, method_name)
            if asyncio.iscoroutinefunction(method):
                setattr(cls, method_name, 
                       lambda self, m=method: run_async_test(m(self)))


if __name__ == "__main__":
    unittest.main()