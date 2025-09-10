"""
Global error handler for UniLinkUp Telegram Bot
"""

import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError, NetworkError, TimedOut, BadRequest

from ui.messages import MessageFormatter

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Global error handler for the bot
    """
    
    def __init__(self, storage_manager=None):
        """
        Initialize error handler
        
        Args:
            storage_manager: Optional storage manager for cleanup
        """
        self.storage_manager = storage_manager
        self.error_count = 0
        self.last_errors = []
        self.max_error_history = 10
    
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle errors that occur during bot operation
        
        Args:
            update: Telegram update object (may be None)
            context: Bot context containing error information
        """
        try:
            error = context.error
            self.error_count += 1
            
            # Log the error with full traceback
            error_msg = f"Error #{self.error_count}: {error}"
            logger.error(error_msg, exc_info=error)
            
            # Store error for debugging
            self._store_error_info(error, update)
            
            # Handle different types of errors
            if isinstance(error, NetworkError):
                await self._handle_network_error(update, context, error)
            elif isinstance(error, TimedOut):
                await self._handle_timeout_error(update, context, error)
            elif isinstance(error, BadRequest):
                await self._handle_bad_request_error(update, context, error)
            elif isinstance(error, TelegramError):
                await self._handle_telegram_error(update, context, error)
            else:
                await self._handle_general_error(update, context, error)
            
            # Cleanup if needed
            await self._cleanup_after_error(update, context, error)
            
        except Exception as handler_error:
            # Error in error handler - log but don't propagate
            logger.critical(f"Error in error handler: {handler_error}", exc_info=True)
    
    def _store_error_info(self, error: Exception, update: Update) -> None:
        """
        Store error information for debugging
        
        Args:
            error: The exception that occurred
            update: Telegram update object
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                "error", logging.ERROR, "", 0, "", (), None
            )) if logger.handlers else "unknown",
            "user_id": update.effective_user.id if update and update.effective_user else None,
            "chat_id": update.effective_chat.id if update and update.effective_chat else None,
            "message_text": update.message.text if update and update.message else None,
            "callback_data": update.callback_query.data if update and update.callback_query else None
        }
        
        # Keep only recent errors
        self.last_errors.append(error_info)
        if len(self.last_errors) > self.max_error_history:
            self.last_errors.pop(0)
    
    async def _handle_network_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  error: NetworkError) -> None:
        """Handle network-related errors"""
        logger.warning(f"Network error: {error}")
        
        # Don't send messages for network errors as they likely won't work
        # Just log and continue
        
    async def _handle_timeout_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  error: TimedOut) -> None:
        """Handle timeout errors"""
        logger.warning(f"Timeout error: {error}")
        
        # Try to send a brief message about the timeout
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⏱️ Request timed out. Please try again."
                )
            except Exception:
                # If we can't send the message, just log it
                logger.warning("Could not send timeout message to user")
    
    async def _handle_bad_request_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                      error: BadRequest) -> None:
        """Handle bad request errors"""
        logger.warning(f"Bad request error: {error}")
        
        # These are usually due to invalid message formats or permissions
        if update and update.effective_chat:
            try:
                error_message = MessageFormatter.format_error_message("general", 
                    "Invalid request. Please start over with /lunch or /study.")
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=error_message
                )
            except Exception:
                logger.warning("Could not send bad request message to user")
    
    async def _handle_telegram_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   error: TelegramError) -> None:
        """Handle general Telegram API errors"""
        logger.error(f"Telegram API error: {error}")
        
        if update and update.effective_chat:
            try:
                error_message = MessageFormatter.format_error_message("general", 
                    "Telegram service error. Please try again in a moment.")
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=error_message
                )
            except Exception:
                logger.warning("Could not send Telegram error message to user")
    
    async def _handle_general_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  error: Exception) -> None:
        """Handle general application errors"""
        logger.error(f"General application error: {error}")
        
        if update and update.effective_chat:
            try:
                error_message = MessageFormatter.format_error_message("general")
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=error_message
                )
            except Exception:
                logger.warning("Could not send general error message to user")
    
    async def _cleanup_after_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 error: Exception) -> None:
        """
        Perform cleanup after an error occurs
        
        Args:
            update: Telegram update object
            context: Bot context
            error: The exception that occurred
        """
        try:
            # Clean up user session if we have storage manager and user info
            if (self.storage_manager and update and update.effective_user):
                user_id = update.effective_user.id
                
                # Get user session and reset it to prevent stuck states
                try:
                    session = self.storage_manager.get_user_session(user_id)
                    if session and session.current_state:
                        session.reset_current_meetup()
                        self.storage_manager.update_user_session(session)
                        logger.info(f"Cleaned up session for user {user_id} after error")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup session after error: {cleanup_error}")
            
            # Answer any pending callback queries to prevent loading indicators
            if update and update.callback_query:
                try:
                    await update.callback_query.answer("Error occurred. Please try again.")
                except Exception:
                    pass  # Ignore if we can't answer
                    
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {cleanup_error}")
    
    def get_error_statistics(self) -> dict:
        """
        Get error statistics for monitoring
        
        Returns:
            dict: Error statistics
        """
        error_types = {}
        for error_info in self.last_errors:
            error_type = error_info["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": self.error_count,
            "recent_errors": len(self.last_errors),
            "error_types": error_types,
            "last_error": self.last_errors[-1] if self.last_errors else None
        }
    
    def reset_error_count(self) -> int:
        """
        Reset error count and return previous count
        
        Returns:
            int: Previous error count
        """
        previous_count = self.error_count
        self.error_count = 0
        self.last_errors.clear()
        return previous_count


# Global error handler instance
_global_error_handler = None


def get_error_handler(storage_manager=None) -> ErrorHandler:
    """
    Get or create global error handler instance
    
    Args:
        storage_manager: Optional storage manager
        
    Returns:
        ErrorHandler: Global error handler instance
    """
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(storage_manager)
    elif storage_manager and not _global_error_handler.storage_manager:
        _global_error_handler.storage_manager = storage_manager
    
    return _global_error_handler


async def global_error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Global error handler function for use with Application.add_error_handler
    
    Args:
        update: Telegram update object
        context: Bot context
    """
    error_handler = get_error_handler()
    await error_handler.handle_error(update, context)


def setup_error_logging() -> None:
    """
    Set up enhanced error logging configuration
    """
    # Create formatter with more detailed information
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Update existing handlers
    for handler in logging.getLogger().handlers:
        handler.setFormatter(formatter)
    
    # Set specific log levels for different components
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    logger.info("Enhanced error logging configured")