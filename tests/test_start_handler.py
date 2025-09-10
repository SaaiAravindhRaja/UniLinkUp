"""
Unit tests for Start command handlers
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from handlers.start import start_command, help_command, StartHandler
from storage.manager import StorageManager
from models.user_session import UserSession


class TestStartCommandFunctions(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.storage = StorageManager()
        
        # Mock update and context
        self.mock_update = Mock()
        self.mock_context = Mock()
        
        # Mock bot_data with storage manager
        self.mock_context.bot_data = {'storage_manager': self.storage}
        
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
        
        # Set up update
        self.mock_update.effective_user = self.mock_user
        self.mock_update.effective_chat = self.mock_chat
        self.mock_update.message = self.mock_message
        
        # Mock bot for typing action
        self.mock_context.bot = Mock()
        self.mock_context.bot.send_chat_action = AsyncMock()
    
    async def test_start_command_success(self):
        """Test successful start command execution"""
        await start_command(self.mock_update, self.mock_context)
        
        # Should reply with welcome message
        self.mock_message.reply_text.assert_called_once()
        
        # Check that welcome message was sent
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("Welcome to UniLinkUp", sent_message)
        self.assertIn("testuser", sent_message)
        
        # Should send typing action
        self.mock_context.bot.send_chat_action.assert_called_once()
        
        # Should create user session
        session = self.storage.get_user_session(12345)
        self.assertEqual(session.username, "testuser")
    
    async def test_start_command_no_storage_manager(self):
        """Test start command with missing storage manager"""
        self.mock_context.bot_data = {}
        
        await start_command(self.mock_update, self.mock_context)
        
        # Should send error message
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("configuration error", sent_message)
    
    async def test_start_command_no_user_id(self):
        """Test start command with no user ID"""
        self.mock_update.effective_user = None
        
        await start_command(self.mock_update, self.mock_context)
        
        # Should handle error gracefully
        self.mock_message.reply_text.assert_called_once()
    
    async def test_help_command_success(self):
        """Test successful help command execution"""
        await help_command(self.mock_update, self.mock_context)
        
        # Should reply with help message
        self.mock_message.reply_text.assert_called_once()
        
        # Check that help message was sent
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("UniLinkUp Help", sent_message)
        self.assertIn("/lunch", sent_message)
        self.assertIn("/study", sent_message)
    
    async def test_help_command_no_storage_manager(self):
        """Test help command with missing storage manager"""
        self.mock_context.bot_data = {}
        
        await help_command(self.mock_update, self.mock_context)
        
        # Should send error message
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("configuration error", sent_message)


class TestStartHandler(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.storage = StorageManager()
        self.handler = StartHandler(self.storage)
        
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
        
        # Set up update
        self.mock_update.effective_user = self.mock_user
        self.mock_update.effective_chat = self.mock_chat
        self.mock_update.message = self.mock_message
        
        # Mock bot for typing action
        self.mock_context.bot = Mock()
        self.mock_context.bot.send_chat_action = AsyncMock()
    
    def test_handler_initialization(self):
        """Test StartHandler initialization"""
        self.assertEqual(self.handler.storage, self.storage)
        self.assertIsNotNone(self.handler.logger)
    
    async def test_handle_start_command_success(self):
        """Test successful start command handling"""
        result = await self.handler.handle_start_command(self.mock_update, self.mock_context)
        
        self.assertTrue(result)
        
        # Should send welcome message
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("Welcome to UniLinkUp", sent_message)
        
        # Should create user session
        session = self.storage.get_user_session(12345)
        self.assertEqual(session.username, "testuser")
        self.assertEqual(session.user_id, 12345)
    
    async def test_handle_start_command_no_user_id(self):
        """Test start command with no user ID"""
        self.mock_update.effective_user = None
        
        result = await self.handler.handle_start_command(self.mock_update, self.mock_context)
        
        self.assertFalse(result)
    
    async def test_handle_start_command_reply_failure(self):
        """Test start command with reply failure"""
        self.mock_message.reply_text.side_effect = Exception("Send failed")
        
        result = await self.handler.handle_start_command(self.mock_update, self.mock_context)
        
        self.assertFalse(result)
    
    async def test_handle_help_command_success(self):
        """Test successful help command handling"""
        result = await self.handler.handle_help_command(self.mock_update, self.mock_context)
        
        self.assertTrue(result)
        
        # Should send help message
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("UniLinkUp Help", sent_message)
    
    async def test_handle_help_command_reply_failure(self):
        """Test help command with reply failure"""
        self.mock_message.reply_text.side_effect = Exception("Send failed")
        
        result = await self.handler.handle_help_command(self.mock_update, self.mock_context)
        
        self.assertFalse(result)
    
    async def test_send_welcome_to_new_user(self):
        """Test sending welcome to new user programmatically"""
        welcome_message = await self.handler.send_welcome_to_new_user(12345, "newuser")
        
        self.assertIn("Welcome to UniLinkUp", welcome_message)
        self.assertIn("newuser", welcome_message)
        
        # Should create user session
        session = self.storage.get_user_session(12345)
        self.assertEqual(session.username, "newuser")
    
    async def test_send_welcome_to_new_user_no_username(self):
        """Test sending welcome to new user without username"""
        welcome_message = await self.handler.send_welcome_to_new_user(67890)
        
        self.assertIn("Welcome to UniLinkUp!", welcome_message)
        # Should not contain personalization
        self.assertNotIn("Welcome to UniLinkUp,", welcome_message)
    
    def test_get_user_session_info(self):
        """Test getting user session information"""
        # Create a user session
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        
        info = self.handler.get_user_session_info(12345)
        
        self.assertEqual(info["user_id"], 12345)
        self.assertEqual(info["username"], "testuser")
        self.assertIn("created_at", info)
        self.assertIn("last_activity", info)
        self.assertIsNone(info["current_state"])
        self.assertFalse(info["has_active_meetup"])  # No location or friends set
    
    def test_get_user_session_info_complete_meetup(self):
        """Test getting session info with complete meetup"""
        # Create a complete meetup
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        session.toggle_friend("Alice")
        
        info = self.handler.get_user_session_info(12345)
        
        self.assertTrue(info["has_active_meetup"])
    
    async def test_start_command_cleans_existing_session(self):
        """Test that start command cleans up existing meetup state"""
        # Create a session with existing meetup data
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        session.toggle_friend("Alice")
        
        # Handle start command
        result = await self.handler.handle_start_command(self.mock_update, self.mock_context)
        
        self.assertTrue(result)
        
        # Session should be cleaned up
        updated_session = self.storage.get_user_session(12345)
        self.assertIsNone(updated_session.meetup_type)
        self.assertIsNone(updated_session.location)
        self.assertEqual(len(updated_session.selected_friends), 0)
    
    async def test_exception_handling_in_start_command(self):
        """Test exception handling in start command"""
        # Mock storage to raise exception
        with patch.object(self.storage, 'get_user_session', side_effect=Exception("Storage error")):
            result = await self.handler.handle_start_command(self.mock_update, self.mock_context)
            
            self.assertFalse(result)
            # Should still send some response to user
            self.mock_message.reply_text.assert_called()


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
for cls in [TestStartCommandFunctions, TestStartHandler]:
    for method_name in dir(cls):
        if method_name.startswith('test_') and 'async' in method_name:
            method = getattr(cls, method_name)
            if asyncio.iscoroutinefunction(method):
                setattr(cls, method_name, 
                       lambda self, m=method: run_async_test(m(self)))


if __name__ == "__main__":
    unittest.main()