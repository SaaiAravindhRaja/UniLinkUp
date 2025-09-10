#!/usr/bin/env python3
"""
UniLinkUp Telegram Bot - Main Entry Point

A Telegram bot to help university students organize meetups with friends.
"""

import logging
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ConversationHandler,
    MessageHandler,
    filters
)

from config.settings import load_bot_token, validate_configuration, get_log_level
from storage.manager import StorageManager
from handlers.start import start_command, help_command
from handlers.recent import recent_command
from handlers.meetup import (
    lunch_command, 
    study_command, 
    cancel_command,
    location_callback,
    time_input,
    time_skip_callback,
    friends_callback,
    confirm_invitation
)
from handlers.error import global_error_handler, get_error_handler, setup_error_logging
from config.constants import ConversationState

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, get_log_level())
)
logger = logging.getLogger(__name__)


def create_conversation_handler() -> ConversationHandler:
    """
    Create and configure the main conversation handler for meetup organization
    
    Returns:
        ConversationHandler: Configured conversation handler
    """
    return ConversationHandler(
        entry_points=[
            CommandHandler("lunch", lunch_command),
            CommandHandler("study", study_command),
        ],
        states={
            ConversationState.LOCATION.value: [
                CallbackQueryHandler(location_callback, pattern=r"^loc_\d+$"),
                CallbackQueryHandler(cancel_command, pattern=r"^confirm_cancel$"),
            ],
            ConversationState.TIME.value: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, time_input),
                CallbackQueryHandler(time_skip_callback, pattern=r"^time_skip$"),
                CallbackQueryHandler(cancel_command, pattern=r"^confirm_cancel$"),
            ],
            ConversationState.FRIENDS.value: [
                CallbackQueryHandler(friends_callback, pattern=r"^friend_\d+$"),
                CallbackQueryHandler(friends_callback, pattern=r"^confirm_(yes|cancel)$"),
                CallbackQueryHandler(cancel_command, pattern=r"^confirm_cancel$"),
            ],
            ConversationState.CONFIRM.value: [
                CallbackQueryHandler(confirm_invitation, pattern=r"^confirm_(send|cancel)$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
        ],
        conversation_timeout=300,  # 5 minutes timeout
        per_chat=True,
        per_user=True,
        per_message=False,
    )


def setup_handlers(application: Application) -> None:
    """Register all command and callback handlers"""
    logger.info("Setting up bot handlers...")
    
    # Set up error handling first
    application.add_error_handler(global_error_handler)
    
    # Basic command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("recent", recent_command))
    
    # Main conversation handler for meetup organization
    conversation_handler = create_conversation_handler()
    application.add_handler(conversation_handler)
    
    # Fallback handlers for unhandled callbacks
    application.add_handler(CallbackQueryHandler(handle_unknown_callback))
    
    # Fallback handler for unhandled messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))
    
    logger.info("Bot handlers configured successfully")


async def handle_unknown_callback(update, context):
    """Handle unknown callback queries"""
    logger.warning(f"Unknown callback query: {update.callback_query.data}")
    await update.callback_query.answer("Unknown action. Please start over with /lunch or /study.")
    await update.callback_query.message.reply_text(
        "⚠️ Unknown action. Please use /lunch or /study to start organizing a meetup."
    )


async def handle_unknown_message(update, context):
    """Handle unknown text messages"""
    logger.info(f"Unknown message from user {update.effective_user.id}: {update.message.text}")
    await update.message.reply_text(
        "🤔 I didn't understand that. Use /help to see available commands or /lunch and /study to organize meetups!"
    )


async def post_init(application: Application) -> None:
    """Initialize bot data after application setup"""
    logger.info("Initializing bot data...")
    
    # Create storage manager
    storage_manager = StorageManager()
    
    # Store in bot_data for access by handlers
    application.bot_data['storage_manager'] = storage_manager
    
    # Initialize error handler with storage manager
    error_handler = get_error_handler(storage_manager)
    application.bot_data['error_handler'] = error_handler
    
    logger.info("Bot data initialized successfully")


async def post_shutdown(application: Application) -> None:
    """Cleanup after bot shutdown"""
    logger.info("Shutting down bot...")
    
    # Get storage manager
    storage_manager = application.bot_data.get('storage_manager')
    
    if storage_manager:
        # Cleanup inactive sessions
        cleaned_sessions = storage_manager.cleanup_inactive_sessions(max_age_hours=1)
        if cleaned_sessions > 0:
            logger.info(f"Cleaned up {cleaned_sessions} inactive sessions")
        
        # Get final statistics
        stats = storage_manager.get_storage_stats()
        logger.info(f"Final stats: {stats}")
    
    logger.info("Bot shutdown complete")


def main() -> None:
    """Initialize and start the bot"""
    logger.info("Starting UniLinkUp Telegram Bot...")
    
    # Set up enhanced error logging
    setup_error_logging()
    
    # Validate configuration
    if not validate_configuration():
        logger.error("Configuration validation failed. Exiting.")
        return
    
    try:
        # Load bot token
        bot_token = load_bot_token()
        
        # Create the Application
        application = Application.builder().token(bot_token).build()
        
        # Set up initialization and cleanup
        application.post_init = post_init
        application.post_shutdown = post_shutdown
        
        # Setup handlers
        setup_handlers(application)
        
        # Start the bot
        logger.info("UniLinkUp bot is ready! Starting polling...")
        application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
            close_loop=False
        )
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    main()