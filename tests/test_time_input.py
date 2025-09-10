"""
Unit tests for time input handling
"""

import unittest
from unittest.mock import Mock, AsyncMock
import asyncio
from telegram.ext import ConversationHandler

from handlers.meetup import MeetupHandler, time_input, time_skip_callback
from storage.manager import StorageManager
from config.constants import ConversationState


class TestTimeInput(unittest.TestCase):
    
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
        
        # Mock message
        self.mock_message = Mock()
        self.mock_message.text = "2:30 PM"
        self.mock_message.reply_text = AsyncMock()
        
        # Set up update
        self.mock_update.effective_user = self.mock_user
        self.mock_update.message = self.mock_message
        
        # Create session with location set
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        session.current_state = ConversationState.TIME
        self.storage.update_user_session(session)
    
    def test_is_valid_time_format(self):
        """Test time format validation"""
        # Valid formats
        self.assertTrue(self.handler._is_valid_time_format("2:30 PM"))
        self.assertTrue(self.handler._is_valid_time_format("14:30"))
        self.assertTrue(self.handler._is_valid_time_format("in 30 minutes"))
        self.assertTrue(self.handler._is_valid_time_format("lunch time"))
        self.assertTrue(self.handler._is_valid_time_format("now"))
        self.assertTrue(self.handler._is_valid_time_format("3 o'clock"))
        
        # Invalid formats
        self.assertFalse(self.handler._is_valid_time_format(""))
        self.assertFalse(self.handler._is_valid_time_format("   "))
        self.assertFalse(self.handler._is_valid_time_format("x"))
        self.assertFalse(self.handler._is_valid_time_format("a" * 50))
    
    async def test_time_input_success(self):
        """Test successful time input"""
        result = await self.handler.time_input(self.mock_update, self.mock_context)
        
        # Should return FRIENDS state
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Should update session with time
        session = self.storage.get_user_session(12345)
        self.assertEqual(session.time, "2:30 PM")
        self.assertEqual(session.current_state, ConversationState.FRIENDS)
        
        # Should send confirmation message
        self.mock_message.reply_text.assert_called_once()
    
    async def test_time_input_invalid_format(self):
        """Test time input with invalid format"""
        self.mock_message.text = "x"
        
        result = await self.handler.time_input(self.mock_update, self.mock_context)
        
        # Should stay in TIME state
        self.assertEqual(result, ConversationState.TIME.value)
        
        # Should send error message
        self.mock_message.reply_text.assert_called_once()
        sent_message = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("Invalid time", sent_message)
    
    async def test_time_input_empty_text(self):
        """Test time input with empty text"""
        self.mock_message.text = ""
        
        result = await self.handler.time_input(self.mock_update, self.mock_context)
        
        # Should stay in TIME state
        self.assertEqual(result, ConversationState.TIME.value)
    
    async def test_time_input_too_long(self):
        """Test time input with too long text"""
        self.mock_message.text = "x" * 100
        
        result = await self.handler.time_input(self.mock_update, self.mock_context)
        
        # Should stay in TIME state
        self.assertEqual(result, ConversationState.TIME.value)
    
    async def test_time_input_no_session(self):
        """Test time input with no session"""
        # Remove session
        self.storage.remove_user_session(12345)
        
        result = await self.handler.time_input(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_time_input_various_formats(self):
        """Test time input with various valid formats"""
        valid_times = [
            "12:30 PM",
            "14:30",
            "in 30 minutes",
            "lunch time",
            "now",
            "soon",
            "3 o'clock",
            "afternoon"
        ]
        
        for time_text in valid_times:
            # Reset session
            session = self.storage.get_user_session(12345)
            session.current_state = ConversationState.TIME
            session.time = None
            self.storage.update_user_session(session)
            
            self.mock_message.text = time_text
            self.mock_message.reply_text.reset_mock()
            
            result = await self.handler.time_input(self.mock_update, self.mock_context)
            
            # Should succeed for all valid formats
            self.assertEqual(result, ConversationState.FRIENDS.value, 
                           f"Failed for time format: {time_text}")
            
            # Check time was set
            updated_session = self.storage.get_user_session(12345)
            self.assertEqual(updated_session.time, time_text)


class TestTimeSkipCallback(unittest.TestCase):
    
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
        self.mock_callback.data = "time_skip"
        self.mock_callback.answer = AsyncMock()
        self.mock_callback.message = Mock()
        self.mock_callback.message.edit_text = AsyncMock()
        self.mock_callback.message.reply_text = AsyncMock()
        
        # Set up update
        self.mock_update.effective_user = self.mock_user
        self.mock_update.callback_query = self.mock_callback
        
        # Create session with location set
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        session.current_state = ConversationState.TIME
        self.storage.update_user_session(session)
    
    async def test_time_skip_callback_success(self):
        """Test successful time skip"""
        result = await self.handler.time_skip_callback(self.mock_update, self.mock_context)
        
        # Should return FRIENDS state
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Should set empty time (flexible)
        session = self.storage.get_user_session(12345)
        self.assertEqual(session.time, "")
        self.assertEqual(session.current_state, ConversationState.FRIENDS)
        
        # Should edit message
        self.mock_callback.message.edit_text.assert_called_once()
        
        # Should answer callback
        self.mock_callback.answer.assert_called_once()
    
    async def test_time_skip_callback_edit_failure(self):
        """Test time skip with edit message failure"""
        # Make edit_text fail
        self.mock_callback.message.edit_text.side_effect = Exception("Edit failed")
        
        result = await self.handler.time_skip_callback(self.mock_update, self.mock_context)
        
        # Should still succeed with fallback
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Should try edit first, then fallback to reply
        self.mock_callback.message.edit_text.assert_called_once()
        self.mock_callback.message.reply_text.assert_called_once()
    
    async def test_time_skip_callback_no_session(self):
        """Test time skip with no session"""
        # Remove session
        self.storage.remove_user_session(12345)
        
        result = await self.handler.time_skip_callback(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)


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
        self.mock_message.text = "2:30 PM"
        self.mock_message.reply_text = AsyncMock()
        
        self.mock_update.effective_user = self.mock_user
        self.mock_update.message = self.mock_message
        
        # Create session
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.set_location("Campus Café")
        session.current_state = ConversationState.TIME
        self.storage.update_user_session(session)
    
    async def test_standalone_time_input(self):
        """Test standalone time input function"""
        result = await time_input(self.mock_update, self.mock_context)
        
        # Should return FRIENDS state
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Should update session
        session = self.storage.get_user_session(12345)
        self.assertEqual(session.time, "2:30 PM")
    
    async def test_standalone_time_skip_callback(self):
        """Test standalone time skip callback function"""
        # Mock callback query
        self.mock_callback = Mock()
        self.mock_callback.data = "time_skip"
        self.mock_callback.answer = AsyncMock()
        self.mock_callback.message = Mock()
        self.mock_callback.message.edit_text = AsyncMock()
        
        self.mock_update.callback_query = self.mock_callback
        
        result = await time_skip_callback(self.mock_update, self.mock_context)
        
        # Should return FRIENDS state
        self.assertEqual(result, ConversationState.FRIENDS.value)
        
        # Should set flexible time
        session = self.storage.get_user_session(12345)
        self.assertEqual(session.time, "")
    
    async def test_standalone_functions_no_storage(self):
        """Test standalone functions with no storage manager"""
        self.mock_context.bot_data = {}
        
        # Test time input
        result = await time_input(self.mock_update, self.mock_context)
        self.assertEqual(result, ConversationHandler.END)
        
        # Test time skip callback
        self.mock_update.callback_query = Mock()
        self.mock_update.callback_query.answer = AsyncMock()
        self.mock_update.callback_query.message = Mock()
        self.mock_update.callback_query.message.reply_text = AsyncMock()
        
        result = await time_skip_callback(self.mock_update, self.mock_context)
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
for cls in [TestTimeInput, TestTimeSkipCallback, TestStandaloneFunctions]:
    for method_name in dir(cls):
        if method_name.startswith('test_') and 'async' in method_name:
            method = getattr(cls, method_name)
            if asyncio.iscoroutinefunction(method):
                setattr(cls, method_name, 
                       lambda self, m=method: run_async_test(m(self)))


if __name__ == "__main__":
    unittest.main()