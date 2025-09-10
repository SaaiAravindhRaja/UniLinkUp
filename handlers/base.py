"""
Base handler class for UniLinkUp Telegram Bot
"""

import logging
from typing import Optional, Any
from telegram import Update
from telegram.ext import ContextTypes

from storage.manager import StorageManager
from ui.messages import MessageFormatter

logger = logging.getLogger(__name__)


class BaseHandler:
    """
    Base class for all bot handlers with common functionality
    """
    
    def __init__(self, storage_manager: StorageManager):
        """
        Initialize base handler
        
        Args:
            storage_manager: Storage manager instance
        """
        self.storage = storage_manager
        self.logger = logger
    
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                          error: Exception, custom_message: str = None) -> None:
        """
        Handle errors gracefully with user feedback
        
        Args:
            update: Telegram update object
            context: Bot context
            error: Exception that occurred
            custom_message: Optional custom error message
        """
        user_id = self._get_user_id(update)
        username = self._get_username(update)
        
        # Log the error
        self.logger.error(
            f"Error in handler for user {user_id} ({username}): {error}",
            exc_info=True
        )
        
        # Send user-friendly error message
        error_message = MessageFormatter.format_error_message("general", custom_message)
        
        try:
            if update.message:
                await update.message.reply_text(error_message)
            elif update.callback_query:
                await update.callback_query.message.reply_text(error_message)
                await update.callback_query.answer()
        except Exception as send_error:
            self.logger.error(f"Failed to send error message: {send_error}")
    
    def _get_user_id(self, update: Update) -> Optional[int]:
        """
        Extract user ID from update
        
        Args:
            update: Telegram update object
            
        Returns:
            Optional[int]: User ID if available
        """
        if update.effective_user:
            return update.effective_user.id
        return None
    
    def _get_username(self, update: Update) -> Optional[str]:
        """
        Extract username from update
        
        Args:
            update: Telegram update object
            
        Returns:
            Optional[str]: Username if available
        """
        if update.effective_user:
            return update.effective_user.username or update.effective_user.first_name
        return None
    
    def _get_chat_id(self, update: Update) -> Optional[int]:
        """
        Extract chat ID from update
        
        Args:
            update: Telegram update object
            
        Returns:
            Optional[int]: Chat ID if available
        """
        if update.effective_chat:
            return update.effective_chat.id
        return None
    
    async def _safe_reply(self, update: Update, text: str, **kwargs) -> bool:
        """
        Safely send a reply message with error handling
        
        Args:
            update: Telegram update object
            text: Message text to send
            **kwargs: Additional arguments for reply_text
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            if update.message:
                await update.message.reply_text(text, **kwargs)
            elif update.callback_query:
                await update.callback_query.message.reply_text(text, **kwargs)
            else:
                self.logger.warning("No message or callback_query in update for reply")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Failed to send reply: {e}")
            return False
    
    async def _safe_edit_message(self, update: Update, text: str, **kwargs) -> bool:
        """
        Safely edit a message with error handling
        
        Args:
            update: Telegram update object
            text: New message text
            **kwargs: Additional arguments for edit_text
            
        Returns:
            bool: True if message was edited successfully
        """
        try:
            if update.callback_query and update.callback_query.message:
                await update.callback_query.message.edit_text(text, **kwargs)
                return True
            else:
                self.logger.warning("No callback_query message to edit")
                return False
        except Exception as e:
            self.logger.error(f"Failed to edit message: {e}")
            return False
    
    async def _safe_answer_callback(self, update: Update, text: str = None) -> bool:
        """
        Safely answer callback query with error handling
        
        Args:
            update: Telegram update object
            text: Optional text to show in popup
            
        Returns:
            bool: True if callback was answered successfully
        """
        try:
            if update.callback_query:
                await update.callback_query.answer(text)
                return True
            else:
                self.logger.warning("No callback_query to answer")
                return False
        except Exception as e:
            self.logger.error(f"Failed to answer callback: {e}")
            return False
    
    def _validate_user_input(self, text: str, max_length: int = 100) -> bool:
        """
        Validate user input text
        
        Args:
            text: Input text to validate
            max_length: Maximum allowed length
            
        Returns:
            bool: True if input is valid
        """
        if not text or not isinstance(text, str):
            return False
        
        if len(text.strip()) == 0:
            return False
        
        if len(text) > max_length:
            return False
        
        return True
    
    def _log_user_action(self, user_id: int, action: str, details: str = None) -> None:
        """
        Log user action for debugging and analytics
        
        Args:
            user_id: User ID
            action: Action performed
            details: Optional additional details
        """
        log_message = f"User {user_id} performed action: {action}"
        if details:
            log_message += f" - {details}"
        
        self.logger.info(log_message)
    
    async def _cleanup_user_session(self, user_id: int, reason: str = "cleanup") -> None:
        """
        Clean up user session with logging
        
        Args:
            user_id: User ID to clean up
            reason: Reason for cleanup
        """
        try:
            session = self.storage.get_user_session(user_id)
            session.reset_current_meetup()
            self.storage.update_user_session(session)
            
            self.logger.info(f"Cleaned up session for user {user_id}: {reason}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup session for user {user_id}: {e}")
    
    def _is_valid_callback_data(self, callback_data: str, expected_prefix: str = None) -> bool:
        """
        Validate callback data format
        
        Args:
            callback_data: Callback data to validate
            expected_prefix: Optional expected prefix
            
        Returns:
            bool: True if callback data is valid
        """
        if not callback_data or not isinstance(callback_data, str):
            return False
        
        if expected_prefix and not callback_data.startswith(expected_prefix):
            return False
        
        return True
    
    async def _send_typing_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Send typing action to show bot is processing
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            bool: True if typing action was sent successfully
        """
        try:
            chat_id = self._get_chat_id(update)
            if chat_id:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to send typing action: {e}")
            return False
    
    def get_storage_manager(self) -> StorageManager:
        """
        Get storage manager instance
        
        Returns:
            StorageManager: Storage manager instance
        """
        return self.storage