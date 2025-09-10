"""
Start command handler for UniLinkUp Telegram Bot
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from handlers.base import BaseHandler
from ui.messages import MessageFormatter

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command - welcome new users and show available commands
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    # Get storage manager from context (will be set up in main.py)
    storage_manager = context.bot_data.get('storage_manager')
    if not storage_manager:
        logger.error("Storage manager not found in bot_data")
        await update.message.reply_text("⚠️ Bot configuration error. Please try again later.")
        return
    
    # Create handler instance for error handling
    handler = BaseHandler(storage_manager)
    
    try:
        # Extract user information
        user_id = handler._get_user_id(update)
        username = handler._get_username(update)
        
        if not user_id:
            await handler.handle_error(update, context, 
                                     Exception("No user ID found"), 
                                     "Unable to identify user")
            return
        
        # Log user action
        handler._log_user_action(user_id, "start_command", f"username: {username}")
        
        # Send typing action
        await handler._send_typing_action(update, context)
        
        # Get or create user session (this initializes the user in our system)
        session = storage_manager.get_user_session(user_id, username)
        
        # Clean up any existing meetup state (fresh start)
        await handler._cleanup_user_session(user_id, "start command")
        
        # Format and send welcome message
        welcome_message = MessageFormatter.format_welcome_message(username)
        
        success = await handler._safe_reply(update, welcome_message)
        
        if success:
            logger.info(f"Welcome message sent to user {user_id} ({username})")
        else:
            logger.warning(f"Failed to send welcome message to user {user_id}")
            
    except Exception as e:
        await handler.handle_error(update, context, e, "Failed to process start command")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /help command - show help information
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    # Get storage manager from context
    storage_manager = context.bot_data.get('storage_manager')
    if not storage_manager:
        logger.error("Storage manager not found in bot_data")
        await update.message.reply_text("⚠️ Bot configuration error. Please try again later.")
        return
    
    # Create handler instance
    handler = BaseHandler(storage_manager)
    
    try:
        user_id = handler._get_user_id(update)
        username = handler._get_username(update)
        
        if user_id:
            handler._log_user_action(user_id, "help_command")
        
        # Send typing action
        await handler._send_typing_action(update, context)
        
        # Format and send help message
        help_message = MessageFormatter.format_help_message()
        
        success = await handler._safe_reply(update, help_message)
        
        if success:
            logger.info(f"Help message sent to user {user_id} ({username})")
        else:
            logger.warning(f"Failed to send help message to user {user_id}")
            
    except Exception as e:
        await handler.handle_error(update, context, e, "Failed to process help command")


class StartHandler(BaseHandler):
    """
    Dedicated handler class for start-related functionality
    """
    
    async def handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Handle start command with full error handling and logging
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            bool: True if command was handled successfully
        """
        try:
            user_id = self._get_user_id(update)
            username = self._get_username(update)
            
            if not user_id:
                await self.handle_error(update, context, 
                                      Exception("No user ID found"), 
                                      "Unable to identify user")
                return False
            
            # Log the start command
            self._log_user_action(user_id, "start_command", f"username: {username}")
            
            # Send typing indicator
            await self._send_typing_action(update, context)
            
            # Initialize or get user session
            session = self.storage.get_user_session(user_id, username)
            
            # Reset any existing meetup state
            await self._cleanup_user_session(user_id, "start command")
            
            # Send welcome message
            welcome_message = MessageFormatter.format_welcome_message(username)
            success = await self._safe_reply(update, welcome_message)
            
            if success:
                self.logger.info(f"Start command completed for user {user_id} ({username})")
                return True
            else:
                self.logger.warning(f"Failed to send welcome message to user {user_id}")
                return False
                
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to process start command")
            return False
    
    async def handle_help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Handle help command with full error handling and logging
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            bool: True if command was handled successfully
        """
        try:
            user_id = self._get_user_id(update)
            username = self._get_username(update)
            
            if user_id:
                self._log_user_action(user_id, "help_command")
            
            # Send typing indicator
            await self._send_typing_action(update, context)
            
            # Send help message
            help_message = MessageFormatter.format_help_message()
            success = await self._safe_reply(update, help_message)
            
            if success:
                self.logger.info(f"Help command completed for user {user_id} ({username})")
                return True
            else:
                self.logger.warning(f"Failed to send help message to user {user_id}")
                return False
                
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to process help command")
            return False
    
    async def send_welcome_to_new_user(self, user_id: int, username: str = None) -> str:
        """
        Send welcome message to a new user (for programmatic use)
        
        Args:
            user_id: User ID
            username: Optional username
            
        Returns:
            str: Welcome message that would be sent
        """
        try:
            # Initialize user session
            session = self.storage.get_user_session(user_id, username)
            
            # Clean up any existing state
            await self._cleanup_user_session(user_id, "new user welcome")
            
            # Generate welcome message
            welcome_message = MessageFormatter.format_welcome_message(username)
            
            self.logger.info(f"Welcome message prepared for new user {user_id} ({username})")
            
            return welcome_message
            
        except Exception as e:
            self.logger.error(f"Failed to prepare welcome for user {user_id}: {e}")
            return MessageFormatter.format_error_message("general")
    
    def get_user_session_info(self, user_id: int) -> dict:
        """
        Get user session information for debugging
        
        Args:
            user_id: User ID
            
        Returns:
            dict: Session information
        """
        try:
            session = self.storage.get_user_session(user_id)
            
            return {
                "user_id": session.user_id,
                "username": session.username,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "current_state": session.current_state.value if session.current_state else None,
                "has_active_meetup": session.is_meetup_complete()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get session info for user {user_id}: {e}")
            return {"error": str(e)}