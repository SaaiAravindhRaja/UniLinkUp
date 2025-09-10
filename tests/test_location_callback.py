"""
Unit tests for location callback handling
"""

import unittest
from unittest.mock import Mock, AsyncMock
import asyncio
from telegram.ext import ConversationHandler

from handlers.meetup import MeetupHandler, location_callback
from storage.manager import StorageManager
from config.constants import ConversationState, LOCATIONS


class TestLocationCallback(unittest.TestCase):
    
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
        self.mock_callback.data = "loc_0"
        self.mock_callback.answer = AsyncMock()
        self.mock_callback.message = Mock()
        self.mock_callback.message.edit_text = AsyncMock()
        self.mock_callback.message.reply_text = AsyncMock()
        
        # Set up update
        self.mock_update.effective_user = self.mock_user
        self.mock_update.callback_query = self.mock_callback
        
        # Create session with meetup started
        session = self.storage.get_user_session(12345, "testuser")
        session.set_meetup_type("lunch")
        session.current_state = ConversationState.LOCATION
        self.storage.update_user_session(session)
    
    async def test_location_callback_success(self):
        """Test successful location selection"""
        result = await self.handler.location_callback(self.mock_update, self.mock_context)
        
        # Should return TIME state
        self.assertEqual(result, ConversationState.TIME.value)
        
        # Should update session with location
        session = self.storage.get_user_session(12345)
        self.assertEqual(session.location, LOCATIONS[0])
        self.assertEqual(session.current_state, ConversationState.TIME)
        
        # Should edit message
        self.mock_callback.message.edit_text.assert_called_once()
        
        # Should answer callback
        self.mock_callback.answer.assert_called_once()
    
    async def test_location_callback_invalid_index(self):
        """Test location callback with invalid index"""
        self.mock_callback.data = "loc_999"
        
        result = await self.handler.location_callback(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_location_callback_invalid_format(self):
        """Test location callback with invalid format"""
        self.mock_callback.data = "invalid_callback"
        
        result = await self.handler.location_callback(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_location_callback_no_session(self):
        """Test location callback with no session"""
        # Remove session
        self.storage.remove_user_session(12345)
        
        result = await self.handler.location_callback(self.mock_update, self.mock_context)
        
        # Should end conversation
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_location_callback_edit_message_fallback(self):
        """Test location callback with edit message failure"""
        # Make edit_text fail
        self.mock_callback.message.edit_text.side_effect = Exception("Edit failed")
        
        result = await self.handler.location_callback(self.mock_update, self.mock_context)
        
        # Should still succeed with fallback
        self.assertEqual(result, ConversationState.TIME.value)
        
        # Should try edit first, then fallback to reply
        self.mock_callback.message.edit_text.assert_called_once()
        self.mock_callback.message.reply_text.assert_called_once()
    
    async def test_standalone_location_callback(self):
        """Test standalone location callback function"""
        self.mock_context.bot_data = {'storage_manager': self.storage}
        
        result = await location_callback(self.mock_update, self.mock_context)
        
        # Should return TIME state
        self.assertEqual(result, ConversationState.TIME.value)
    
    async def test_standalone_location_callback_no_storage(self):
        """Test standalone location callback with no storage"""
        self.mock_context.bot_data = {}
        
        result = await location_callback(self.mock_update, self.mock_context)
        
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
for method_name in dir(TestLocationCallback):
    if method_name.startswith('test_') and 'async' in method_name:
        method = getattr(TestLocationCallback, method_name)
        if asyncio.iscoroutinefunction(method):
            setattr(TestLocationCallback, method_name, 
                   lambda self, m=method: run_async_test(m(self)))


if __name__ == "__main__":
    unittest.main()