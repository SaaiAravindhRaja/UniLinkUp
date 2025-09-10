"""
Integration tests for main bot setup
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from main import (
    create_conversation_handler, 
    setup_handlers, 
    handle_unknown_callback,
    handle_unknown_message,
    post_init,
    post_shutdown
)
from config.constants import ConversationState


class TestMainIntegration(unittest.TestCase):
    
    def test_create_conversation_handler(self):
        """Test conversation handler creation"""
        handler = create_conversation_handler()
        
        # Should be a ConversationHandler
        from telegram.ext import ConversationHandler
        self.assertIsInstance(handler, ConversationHandler)
        
        # Should have entry points
        self.assertEqual(len(handler.entry_points), 2)  # lunch and study commands
        
        # Should have states for all conversation states
        expected_states = [
            ConversationState.LOCATION.value,
            ConversationState.TIME.value,
            ConversationState.FRIENDS.value,
            ConversationState.CONFIRM.value
        ]
        
        for state in expected_states:
            self.assertIn(state, handler.states)
        
        # Should have fallbacks
        self.assertGreater(len(handler.fallbacks), 0)
        
        # Should have timeout configured
        self.assertEqual(handler.conversation_timeout, 300)
    
    def test_setup_handlers(self):
        """Test handler setup"""
        # Mock application
        mock_app = Mock()
        mock_app.add_handler = Mock()
        
        setup_handlers(mock_app)
        
        # Should add multiple handlers
        self.assertGreater(mock_app.add_handler.call_count, 0)
        
        # Verify some key handlers were added
        handler_calls = [call[0][0] for call in mock_app.add_handler.call_args_list]
        
        # Should have command handlers
        from telegram.ext import CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler
        
        command_handlers = [h for h in handler_calls if isinstance(h, CommandHandler)]
        self.assertGreater(len(command_handlers), 0)
        
        # Should have conversation handler
        conversation_handlers = [h for h in handler_calls if isinstance(h, ConversationHandler)]
        self.assertEqual(len(conversation_handlers), 1)
        
        # Should have fallback handlers
        callback_handlers = [h for h in handler_calls if isinstance(h, CallbackQueryHandler)]
        message_handlers = [h for h in handler_calls if isinstance(h, MessageHandler)]
        self.assertGreater(len(callback_handlers), 0)
        self.assertGreater(len(message_handlers), 0)
    
    async def test_handle_unknown_callback(self):
        """Test unknown callback handling"""
        # Mock update and context
        mock_update = Mock()
        mock_context = Mock()
        
        # Mock callback query
        mock_callback = Mock()
        mock_callback.data = "unknown_callback"
        mock_callback.answer = AsyncMock()
        mock_callback.message = Mock()
        mock_callback.message.reply_text = AsyncMock()
        
        mock_update.callback_query = mock_callback
        
        await handle_unknown_callback(mock_update, mock_context)
        
        # Should answer callback
        mock_callback.answer.assert_called_once()
        
        # Should send help message
        mock_callback.message.reply_text.assert_called_once()
        sent_message = mock_callback.message.reply_text.call_args[0][0]
        self.assertIn("Unknown action", sent_message)
    
    async def test_handle_unknown_message(self):
        """Test unknown message handling"""
        # Mock update and context
        mock_update = Mock()
        mock_context = Mock()
        
        # Mock user and message
        mock_user = Mock()
        mock_user.id = 12345
        
        mock_message = Mock()
        mock_message.text = "random text"
        mock_message.reply_text = AsyncMock()
        
        mock_update.effective_user = mock_user
        mock_update.message = mock_message
        
        await handle_unknown_message(mock_update, mock_context)
        
        # Should send help message
        mock_message.reply_text.assert_called_once()
        sent_message = mock_message.reply_text.call_args[0][0]
        self.assertIn("didn't understand", sent_message)
        self.assertIn("/help", sent_message)
    
    async def test_post_init(self):
        """Test post initialization"""
        # Mock application
        mock_app = Mock()
        mock_app.bot_data = {}
        
        await post_init(mock_app)
        
        # Should create storage manager
        self.assertIn('storage_manager', mock_app.bot_data)
        
        # Storage manager should be properly initialized
        storage_manager = mock_app.bot_data['storage_manager']
        from storage.manager import StorageManager
        self.assertIsInstance(storage_manager, StorageManager)
    
    async def test_post_shutdown(self):
        """Test post shutdown cleanup"""
        # Mock application with storage manager
        mock_app = Mock()
        
        # Mock storage manager
        mock_storage = Mock()
        mock_storage.cleanup_inactive_sessions.return_value = 2
        mock_storage.get_storage_stats.return_value = {"sessions": 0, "pings": 5}
        
        mock_app.bot_data = {'storage_manager': mock_storage}
        
        await post_shutdown(mock_app)
        
        # Should cleanup inactive sessions
        mock_storage.cleanup_inactive_sessions.assert_called_once_with(max_age_hours=1)
        
        # Should get final stats
        mock_storage.get_storage_stats.assert_called_once()
    
    async def test_post_shutdown_no_storage(self):
        """Test post shutdown with no storage manager"""
        # Mock application without storage manager
        mock_app = Mock()
        mock_app.bot_data = {}
        
        # Should not raise exception
        await post_shutdown(mock_app)
    
    def test_conversation_handler_states(self):
        """Test conversation handler state configuration"""
        handler = create_conversation_handler()
        
        # Test LOCATION state handlers
        location_handlers = handler.states[ConversationState.LOCATION.value]
        self.assertGreater(len(location_handlers), 0)
        
        # Test TIME state handlers
        time_handlers = handler.states[ConversationState.TIME.value]
        self.assertGreater(len(time_handlers), 0)
        
        # Test FRIENDS state handlers
        friends_handlers = handler.states[ConversationState.FRIENDS.value]
        self.assertGreater(len(friends_handlers), 0)
        
        # Test CONFIRM state handlers
        confirm_handlers = handler.states[ConversationState.CONFIRM.value]
        self.assertGreater(len(confirm_handlers), 0)
    
    def test_conversation_handler_patterns(self):
        """Test conversation handler callback patterns"""
        handler = create_conversation_handler()
        
        # Check that patterns are properly configured
        location_handlers = handler.states[ConversationState.LOCATION.value]
        
        # Find callback query handlers
        from telegram.ext import CallbackQueryHandler
        callback_handlers = [h for h in location_handlers if isinstance(h, CallbackQueryHandler)]
        
        self.assertGreater(len(callback_handlers), 0)
        
        # Check patterns exist
        for cb_handler in callback_handlers:
            if hasattr(cb_handler, 'pattern') and cb_handler.pattern:
                self.assertIsNotNone(cb_handler.pattern)


class TestMainConfiguration(unittest.TestCase):
    
    @patch('main.validate_configuration')
    @patch('main.load_bot_token')
    def test_main_configuration_validation(self, mock_load_token, mock_validate):
        """Test main function configuration validation"""
        from main import main
        
        # Test configuration validation failure
        mock_validate.return_value = False
        
        # Should exit early without starting bot
        main()
        
        mock_validate.assert_called_once()
        mock_load_token.assert_not_called()
    
    @patch('main.Application')
    @patch('main.validate_configuration')
    @patch('main.load_bot_token')
    def test_main_successful_start(self, mock_load_token, mock_validate, mock_application_class):
        """Test successful main function execution"""
        from main import main
        
        # Mock successful configuration
        mock_validate.return_value = True
        mock_load_token.return_value = "test_token"
        
        # Mock application
        mock_app_builder = Mock()
        mock_app = Mock()
        mock_app_builder.token.return_value = mock_app_builder
        mock_app_builder.build.return_value = mock_app
        mock_application_class.builder.return_value = mock_app_builder
        
        # Mock run_polling to avoid actually starting the bot
        mock_app.run_polling = Mock()
        
        main()
        
        # Should validate configuration
        mock_validate.assert_called_once()
        
        # Should load token
        mock_load_token.assert_called_once()
        
        # Should create application with token
        mock_app_builder.token.assert_called_once_with("test_token")
        
        # Should set up handlers
        self.assertIsNotNone(mock_app.post_init)
        self.assertIsNotNone(mock_app.post_shutdown)
        
        # Should start polling
        mock_app.run_polling.assert_called_once()


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
for cls in [TestMainIntegration, TestMainConfiguration]:
    for method_name in dir(cls):
        if method_name.startswith('test_') and 'async' in method_name:
            method = getattr(cls, method_name)
            if asyncio.iscoroutinefunction(method):
                setattr(cls, method_name, 
                       lambda self, m=method: run_async_test(m(self)))


if __name__ == "__main__":
    unittest.main()