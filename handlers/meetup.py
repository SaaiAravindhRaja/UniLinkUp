"""
Meetup handler for UniLinkUp Telegram Bot
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from handlers.base import BaseHandler
from ui.messages import MessageFormatter
from ui.keyboards import KeyboardFactory
from config.constants import ConversationState
from models.user_session import UserSession
from models.ping import PingRecord

logger = logging.getLogger(__name__)


class MeetupHandler(BaseHandler):
    """
    Handler for meetup organization conversations (lunch and study sessions)
    """
    
    def __init__(self, storage_manager):
        """
        Initialize meetup handler
        
        Args:
            storage_manager: Storage manager instance
        """
        super().__init__(storage_manager)
        self.keyboard_factory = KeyboardFactory()
    
    async def lunch_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle /lunch command - start lunch meetup organization
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            int: Next conversation state
        """
        return await self._start_meetup_conversation(update, context, "lunch")
    
    async def study_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle /study command - start study session organization
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            int: Next conversation state
        """
        return await self._start_meetup_conversation(update, context, "study")
    
    async def _start_meetup_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                       meetup_type: str) -> int:
        """
        Start a meetup organization conversation
        
        Args:
            update: Telegram update object
            context: Bot context
            meetup_type: Type of meetup ("lunch" or "study")
            
        Returns:
            int: Next conversation state or ConversationHandler.END
        """
        try:
            user_id = self._get_user_id(update)
            username = self._get_username(update)
            
            if not user_id:
                await self.handle_error(update, context, 
                                      Exception("No user ID found"), 
                                      "Unable to identify user")
                return ConversationHandler.END
            
            # Log the command
            self._log_user_action(user_id, f"{meetup_type}_command", f"username: {username}")
            
            # Send typing action
            await self._send_typing_action(update, context)
            
            # Get or create user session
            session = self.storage.get_user_session(user_id, username)
            
            # Reset any existing meetup state
            session.reset_current_meetup()
            
            # Set meetup type and initial state
            session.set_meetup_type(meetup_type)
            session.current_state = ConversationState.LOCATION
            
            # Update session in storage
            self.storage.update_user_session(session)
            
            # Send meetup prompt with location keyboard
            prompt_message = MessageFormatter.format_meetup_prompt(meetup_type)
            location_keyboard = self.keyboard_factory.create_location_keyboard()
            
            success = await self._safe_reply(
                update, 
                prompt_message, 
                reply_markup=location_keyboard
            )
            
            if success:
                self.logger.info(f"{meetup_type.title()} conversation started for user {user_id}")
                return ConversationState.LOCATION.value
            else:
                self.logger.warning(f"Failed to start {meetup_type} conversation for user {user_id}")
                await self._cleanup_user_session(user_id, f"failed {meetup_type} start")
                return ConversationHandler.END
                
        except Exception as e:
            await self.handle_error(update, context, e, f"Failed to start {meetup_type} meetup")
            return ConversationHandler.END
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle conversation cancellation
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            int: ConversationHandler.END
        """
        try:
            user_id = self._get_user_id(update)
            
            if user_id:
                self._log_user_action(user_id, "cancel_conversation")
                await self._cleanup_user_session(user_id, "user cancellation")
            
            # Send cancellation message
            cancel_message = MessageFormatter.format_cancel_message()
            await self._safe_reply(update, cancel_message)
            
            # Answer callback if it's a callback query
            if update.callback_query:
                await self._safe_answer_callback(update, "Cancelled")
            
            self.logger.info(f"Conversation cancelled for user {user_id}")
            
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to cancel conversation")
        
        return ConversationHandler.END
    
    async def timeout_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle conversation timeout
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            int: ConversationHandler.END
        """
        try:
            user_id = self._get_user_id(update)
            
            if user_id:
                self._log_user_action(user_id, "conversation_timeout")
                await self._cleanup_user_session(user_id, "conversation timeout")
            
            # Send timeout message
            timeout_message = MessageFormatter.format_error_message("timeout")
            await self._safe_reply(update, timeout_message)
            
            self.logger.info(f"Conversation timed out for user {user_id}")
            
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to handle timeout")
        
        return ConversationHandler.END
    
    def get_conversation_state_value(self, state: ConversationState) -> int:
        """
        Get integer value for conversation state (for ConversationHandler)
        
        Args:
            state: ConversationState enum value
            
        Returns:
            int: State value for ConversationHandler
        """
        state_mapping = {
            ConversationState.LOCATION: 1,
            ConversationState.TIME: 2,
            ConversationState.FRIENDS: 3,
            ConversationState.CONFIRM: 4
        }
        return state_mapping.get(state, 0)
    
    def get_user_session_safely(self, user_id: int) -> UserSession:
        """
        Safely get user session with error handling
        
        Args:
            user_id: User ID
            
        Returns:
            UserSession: User session or None if error
        """
        try:
            return self.storage.get_user_session(user_id)
        except Exception as e:
            self.logger.error(f"Failed to get session for user {user_id}: {e}")
            return None
    
    async def handle_invalid_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle invalid conversation state
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            int: ConversationHandler.END
        """
        try:
            user_id = self._get_user_id(update)
            
            if user_id:
                self._log_user_action(user_id, "invalid_conversation_state")
                await self._cleanup_user_session(user_id, "invalid state")
            
            # Send error message and suggest restart
            error_message = (
                "⚠️ Something went wrong with the conversation. "
                "Please start over with /lunch or /study."
            )
            await self._safe_reply(update, error_message)
            
            # Answer callback if needed
            if update.callback_query:
                await self._safe_answer_callback(update, "Please start over")
            
            self.logger.warning(f"Invalid conversation state for user {user_id}")
            
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to handle invalid state")
        
        return ConversationHandler.END
    
    def validate_meetup_session(self, session: UserSession) -> tuple[bool, str]:
        """
        Validate that a meetup session has required data
        
        Args:
            session: User session to validate
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        if not session:
            return False, "No session found"
        
        if not session.meetup_type:
            return False, "No meetup type set"
        
        if session.meetup_type not in ["lunch", "study"]:
            return False, f"Invalid meetup type: {session.meetup_type}"
        
        return True, ""
    
    async def location_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle location selection from inline keyboard
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            int: Next conversation state
        """
        try:
            user_id = self._get_user_id(update)
            
            if not user_id or not update.callback_query:
                await self.handle_error(update, context, 
                                      Exception("Invalid callback query"), 
                                      "Invalid selection")
                return ConversationHandler.END
            
            callback_data = update.callback_query.data
            
            # Parse callback data
            action, param = self.keyboard_factory.parse_callback_data(callback_data)
            
            if action != "location" or not param:
                await self.handle_error(update, context, 
                                      Exception(f"Invalid location callback: {callback_data}"), 
                                      "Invalid location selection")
                return ConversationHandler.END
            
            # Get location by index
            try:
                location_index = int(param)
                location = self.keyboard_factory.get_location_by_index(location_index)
            except (ValueError, TypeError):
                await self.handle_error(update, context, 
                                      Exception(f"Invalid location index: {param}"), 
                                      "Invalid location selection")
                return ConversationHandler.END
            
            if not location:
                await self.handle_error(update, context, 
                                      Exception(f"Location not found for index: {location_index}"), 
                                      "Location not found")
                return ConversationHandler.END
            
            # Get user session
            session = self.get_user_session_safely(user_id)
            if not session:
                await self.handle_error(update, context, 
                                      Exception("Session not found"), 
                                      "Session expired. Please start over.")
                return ConversationHandler.END
            
            # Validate session state
            is_valid, error_msg = self.validate_meetup_session(session)
            if not is_valid:
                await self.handle_error(update, context, 
                                      Exception(f"Invalid session: {error_msg}"), 
                                      "Session error. Please start over.")
                return ConversationHandler.END
            
            # Update session with selected location
            session.set_location(location)
            session.current_state = ConversationState.TIME
            self.storage.update_user_session(session)
            
            # Log the selection
            self._log_user_action(user_id, "location_selected", f"location: {location}")
            
            # Send confirmation and time prompt
            confirmation_message = MessageFormatter.format_location_selected_message(location)
            time_keyboard = self.keyboard_factory.create_time_skip_keyboard()
            
            # Edit the message to show selection
            success = await self._safe_edit_message(
                update, 
                confirmation_message, 
                reply_markup=time_keyboard
            )
            
            if not success:
                # Fallback to new message if edit fails
                success = await self._safe_reply(
                    update, 
                    confirmation_message, 
                    reply_markup=time_keyboard
                )
            
            # Answer the callback query
            await self._safe_answer_callback(update, f"Selected: {location}")
            
            if success:
                self.logger.info(f"Location '{location}' selected for user {user_id}")
                return ConversationState.TIME.value
            else:
                self.logger.warning(f"Failed to send time prompt for user {user_id}")
                await self._cleanup_user_session(user_id, "failed location selection")
                return ConversationHandler.END
                
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to process location selection")
            return ConversationHandler.END
    
    async def time_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle time input from user message
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            int: Next conversation state
        """
        try:
            user_id = self._get_user_id(update)
            
            if not user_id or not update.message:
                await self.handle_error(update, context, 
                                      Exception("Invalid message"), 
                                      "Invalid input")
                return ConversationHandler.END
            
            # Get user session
            session = self.get_user_session_safely(user_id)
            if not session:
                await self.handle_error(update, context, 
                                      Exception("Session not found"), 
                                      "Session expired. Please start over.")
                return ConversationHandler.END
            
            # Validate session state
            is_valid, error_msg = self.validate_meetup_session(session)
            if not is_valid:
                await self.handle_error(update, context, 
                                      Exception(f"Invalid session: {error_msg}"), 
                                      "Session error. Please start over.")
                return ConversationHandler.END
            
            # Get time input
            time_text = update.message.text.strip()
            
            # Validate time input
            if not self._validate_user_input(time_text, max_length=50):
                error_message = MessageFormatter.format_error_message("invalid_time")
                await self._safe_reply(update, error_message)
                return ConversationState.TIME.value  # Stay in TIME state
            
            # Basic time format validation
            if not self._is_valid_time_format(time_text):
                error_message = MessageFormatter.format_error_message("invalid_time")
                await self._safe_reply(update, error_message)
                return ConversationState.TIME.value  # Stay in TIME state
            
            # Update session with time
            session.set_time(time_text)
            session.current_state = ConversationState.FRIENDS
            self.storage.update_user_session(session)
            
            # Log the input
            self._log_user_action(user_id, "time_input", f"time: {time_text}")
            
            # Send confirmation and friends selection
            confirmation_message = MessageFormatter.format_time_set_message(time_text)
            friends_keyboard = self.keyboard_factory.create_friends_keyboard(session)
            
            success = await self._safe_reply(
                update, 
                confirmation_message, 
                reply_markup=friends_keyboard
            )
            
            if success:
                self.logger.info(f"Time '{time_text}' set for user {user_id}")
                return ConversationState.FRIENDS.value
            else:
                self.logger.warning(f"Failed to send friends selection for user {user_id}")
                await self._cleanup_user_session(user_id, "failed time input")
                return ConversationHandler.END
                
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to process time input")
            return ConversationHandler.END
    
    async def time_skip_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle time skip callback (flexible time)
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            int: Next conversation state
        """
        try:
            user_id = self._get_user_id(update)
            
            if not user_id or not update.callback_query:
                await self.handle_error(update, context, 
                                      Exception("Invalid callback query"), 
                                      "Invalid selection")
                return ConversationHandler.END
            
            # Get user session
            session = self.get_user_session_safely(user_id)
            if not session:
                await self.handle_error(update, context, 
                                      Exception("Session not found"), 
                                      "Session expired. Please start over.")
                return ConversationHandler.END
            
            # Set flexible time (empty string)
            session.set_time("")
            session.current_state = ConversationState.FRIENDS
            self.storage.update_user_session(session)
            
            # Log the skip
            self._log_user_action(user_id, "time_skipped", "flexible time")
            
            # Send friends selection
            friends_message = MessageFormatter.format_time_set_message("")
            friends_keyboard = self.keyboard_factory.create_friends_keyboard(session)
            
            # Edit the message
            success = await self._safe_edit_message(
                update, 
                friends_message, 
                reply_markup=friends_keyboard
            )
            
            if not success:
                # Fallback to new message
                success = await self._safe_reply(
                    update, 
                    friends_message, 
                    reply_markup=friends_keyboard
                )
            
            # Answer the callback query
            await self._safe_answer_callback(update, "Time set to flexible")
            
            if success:
                self.logger.info(f"Time skipped (flexible) for user {user_id}")
                return ConversationState.FRIENDS.value
            else:
                self.logger.warning(f"Failed to send friends selection for user {user_id}")
                await self._cleanup_user_session(user_id, "failed time skip")
                return ConversationHandler.END
                
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to process time skip")
            return ConversationHandler.END
    
    def _is_valid_time_format(self, time_text: str) -> bool:
        """
        Validate time format (basic validation)
        
        Args:
            time_text: Time string to validate
            
        Returns:
            bool: True if format seems valid
        """
        if not time_text or len(time_text.strip()) == 0:
            return False
        
        # Allow various time formats - be flexible
        time_lower = time_text.lower().strip()
        
        # Common time patterns
        valid_patterns = [
            # Standard time formats
            r'\d{1,2}:\d{2}\s*(am|pm)?',
            # Relative time
            r'in\s+\d+\s+(minutes?|hours?)',
            # Natural language
            r'(now|soon|later|afternoon|evening|morning)',
            # Specific times
            r'(lunch|dinner|breakfast)\s*time',
        ]
        
        import re
        for pattern in valid_patterns:
            if re.search(pattern, time_lower):
                return True
        
        # If it contains numbers and common time words, probably valid
        if any(char.isdigit() for char in time_text):
            time_words = ['am', 'pm', 'hour', 'minute', 'o\'clock', ':', 'at']
            if any(word in time_lower for word in time_words):
                return True
        
        # Allow short reasonable text
        if 3 <= len(time_text.strip()) <= 30:
            return True
        
        return False
    
    async def friends_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle friends selection from inline keyboard
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            int: Next conversation state or same state for continued selection
        """
        try:
            user_id = self._get_user_id(update)
            
            if not user_id or not update.callback_query:
                await self.handle_error(update, context, 
                                      Exception("Invalid callback query"), 
                                      "Invalid selection")
                return ConversationHandler.END
            
            callback_data = update.callback_query.data
            
            # Parse callback data
            action, param = self.keyboard_factory.parse_callback_data(callback_data)
            
            # Get user session
            session = self.get_user_session_safely(user_id)
            if not session:
                await self.handle_error(update, context, 
                                      Exception("Session not found"), 
                                      "Session expired. Please start over.")
                return ConversationHandler.END
            
            # Handle different callback actions
            if action == "friend" and param:
                return await self._handle_friend_toggle(update, context, session, param)
            elif action == "confirm" and param:
                return await self._handle_friends_confirmation(update, context, session, param)
            else:
                await self.handle_error(update, context, 
                                      Exception(f"Invalid friends callback: {callback_data}"), 
                                      "Invalid selection")
                return ConversationHandler.END
                
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to process friends selection")
            return ConversationHandler.END
    
    async def _handle_friend_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  session: UserSession, friend_index_str: str) -> int:
        """
        Handle toggling a friend selection
        
        Args:
            update: Telegram update object
            context: Bot context
            session: User session
            friend_index_str: Friend index as string
            
        Returns:
            int: Conversation state
        """
        try:
            # Get friend by index
            friend_index = int(friend_index_str)
            friend_name = self.keyboard_factory.get_friend_by_index(friend_index)
        except (ValueError, TypeError):
            await self.handle_error(update, context, 
                                  Exception(f"Invalid friend index: {friend_index_str}"), 
                                  "Invalid friend selection")
            return ConversationHandler.END
        
        if not friend_name:
            await self.handle_error(update, context, 
                                  Exception(f"Friend not found for index: {friend_index}"), 
                                  "Friend not found")
            return ConversationHandler.END
        
        # Toggle friend selection
        was_added = session.toggle_friend(friend_name)
        self.storage.update_user_session(session)
        
        # Log the toggle
        action_type = "added" if was_added else "removed"
        self._log_user_action(session.user_id, f"friend_{action_type}", f"friend: {friend_name}")
        
        # Update the keyboard with new selection state
        updated_message = MessageFormatter.format_friends_updated_message(session)
        updated_keyboard = self.keyboard_factory.create_friends_keyboard(session)
        
        # Edit the message with updated keyboard
        success = await self._safe_edit_message(
            update, 
            updated_message, 
            reply_markup=updated_keyboard
        )
        
        if not success:
            # Fallback to new message if edit fails
            success = await self._safe_reply(
                update, 
                updated_message, 
                reply_markup=updated_keyboard
            )
        
        # Answer the callback query with feedback
        callback_text = f"{'Added' if was_added else 'Removed'} {friend_name}"
        await self._safe_answer_callback(update, callback_text)
        
        if success:
            self.logger.info(f"Friend '{friend_name}' {action_type} for user {session.user_id}")
            return ConversationState.FRIENDS.value  # Stay in friends selection
        else:
            self.logger.warning(f"Failed to update friends selection for user {session.user_id}")
            await self._cleanup_user_session(session.user_id, "failed friend toggle")
            return ConversationHandler.END
    
    async def _handle_friends_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                         session: UserSession, action: str) -> int:
        """
        Handle friends selection confirmation or cancellation
        
        Args:
            update: Telegram update object
            context: Bot context
            session: User session
            action: Confirmation action ("yes", "cancel")
            
        Returns:
            int: Next conversation state
        """
        if action == "cancel":
            # Cancel the entire conversation
            return await self.cancel_conversation(update, context)
        
        elif action == "yes":
            # Validate that at least one friend is selected
            if len(session.selected_friends) == 0:
                error_message = MessageFormatter.format_error_message("no_friends")
                await self._safe_reply(update, error_message)
                await self._safe_answer_callback(update, "Please select at least one friend")
                return ConversationState.FRIENDS.value  # Stay in friends selection
            
            # Move to confirmation state
            session.current_state = ConversationState.CONFIRM
            self.storage.update_user_session(session)
            
            # Log the confirmation
            self._log_user_action(session.user_id, "friends_confirmed", 
                                f"selected: {len(session.selected_friends)} friends")
            
            # Send final confirmation message
            confirmation_message = MessageFormatter.format_confirmation_message(session)
            confirmation_keyboard = self.keyboard_factory.create_confirmation_keyboard()
            
            # Edit the message to show confirmation
            success = await self._safe_edit_message(
                update, 
                confirmation_message, 
                reply_markup=confirmation_keyboard
            )
            
            if not success:
                # Fallback to new message
                success = await self._safe_reply(
                    update, 
                    confirmation_message, 
                    reply_markup=confirmation_keyboard
                )
            
            # Answer the callback query
            await self._safe_answer_callback(update, "Ready to send invitations!")
            
            if success:
                self.logger.info(f"Friends confirmed for user {session.user_id}, moving to final confirmation")
                return ConversationState.CONFIRM.value
            else:
                self.logger.warning(f"Failed to send confirmation for user {session.user_id}")
                await self._cleanup_user_session(session.user_id, "failed friends confirmation")
                return ConversationHandler.END
        
        else:
            await self.handle_error(update, context, 
                                  Exception(f"Invalid confirmation action: {action}"), 
                                  "Invalid action")
            return ConversationHandler.END
    
    async def confirm_invitation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle final invitation confirmation and sending
        
        Args:
            update: Telegram update object
            context: Bot context
            
        Returns:
            int: ConversationHandler.END (conversation complete)
        """
        try:
            user_id = self._get_user_id(update)
            
            if not user_id or not update.callback_query:
                await self.handle_error(update, context, 
                                      Exception("Invalid callback query"), 
                                      "Invalid confirmation")
                return ConversationHandler.END
            
            callback_data = update.callback_query.data
            
            # Parse callback data
            action, param = self.keyboard_factory.parse_callback_data(callback_data)
            
            if action != "confirm":
                await self.handle_error(update, context, 
                                      Exception(f"Invalid confirm callback: {callback_data}"), 
                                      "Invalid confirmation")
                return ConversationHandler.END
            
            # Get user session
            session = self.get_user_session_safely(user_id)
            if not session:
                await self.handle_error(update, context, 
                                      Exception("Session not found"), 
                                      "Session expired. Please start over.")
                return ConversationHandler.END
            
            # Handle different confirmation actions
            if param == "send":
                return await self._send_invitations(update, context, session)
            elif param == "cancel":
                return await self.cancel_conversation(update, context)
            else:
                await self.handle_error(update, context, 
                                      Exception(f"Invalid confirmation action: {param}"), 
                                      "Invalid action")
                return ConversationHandler.END
                
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to process confirmation")
            return ConversationHandler.END
    
    async def _send_invitations(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              session: UserSession) -> int:
        """
        Send invitations and complete the meetup organization
        
        Args:
            update: Telegram update object
            context: Bot context
            session: User session with complete meetup data
            
        Returns:
            int: ConversationHandler.END
        """
        try:
            # Validate that meetup is complete
            if not session.is_meetup_complete():
                await self.handle_error(update, context, 
                                      Exception("Incomplete meetup data"), 
                                      "Meetup information is incomplete")
                return ConversationHandler.END
            
            # Create ping record
            from models.ping import PingRecord
            
            ping = PingRecord(
                organizer_id=session.user_id,
                organizer_name=session.username or f"User{session.user_id}",
                meetup_type=session.meetup_type,
                location=session.location,
                time=session.time or "",
                invited_friends=session.selected_friends.copy()
            )
            
            # Save ping to storage
            self.storage.save_ping(ping)
            
            # Log the invitation
            self._log_user_action(session.user_id, "invitations_sent", 
                                f"type: {session.meetup_type}, friends: {len(session.selected_friends)}")
            
            # Generate notifications for each friend (simulated)
            notifications = []
            for friend_name in session.selected_friends:
                notification = MessageFormatter.format_invitation_notification(ping, friend_name)
                notifications.append(f"📨 **To {friend_name}:**\n{notification}")
            
            # Create success message
            success_message = MessageFormatter.format_invitation_sent_message(len(session.selected_friends))
            
            # Add notification preview
            if notifications:
                success_message += "\n\n🔔 **Notifications sent:**\n\n"
                success_message += "\n\n".join(notifications[:3])  # Show first 3
                
                if len(notifications) > 3:
                    success_message += f"\n\n... and {len(notifications) - 3} more"
            
            # Send success message
            success = await self._safe_edit_message(update, success_message)
            
            if not success:
                # Fallback to new message
                success = await self._safe_reply(update, success_message)
            
            # Answer the callback query
            await self._safe_answer_callback(update, "Invitations sent!")
            
            # Clean up session
            await self._cleanup_user_session(session.user_id, "invitations sent")
            
            if success:
                self.logger.info(f"Invitations sent successfully for user {session.user_id}")
            else:
                self.logger.warning(f"Failed to send success message for user {session.user_id}")
            
            return ConversationHandler.END
            
        except Exception as e:
            await self.handle_error(update, context, e, "Failed to send invitations")
            return ConversationHandler.END
    
    def create_notification_preview(self, ping: PingRecord, max_friends: int = 3) -> str:
        """
        Create a preview of notifications that would be sent
        
        Args:
            ping: Ping record containing invitation details
            max_friends: Maximum number of friend notifications to show
            
        Returns:
            str: Formatted notification preview
        """
        notifications = []
        
        for i, friend_name in enumerate(ping.invited_friends[:max_friends]):
            notification = MessageFormatter.format_invitation_notification(ping, friend_name)
            notifications.append(f"📨 **To {friend_name}:**\n{notification}")
        
        preview = "\n\n".join(notifications)
        
        if len(ping.invited_friends) > max_friends:
            remaining = len(ping.invited_friends) - max_friends
            preview += f"\n\n... and {remaining} more friend{'s' if remaining != 1 else ''}"
        
        return preview
    
    async def send_state_debug_info(self, update: Update, user_id: int) -> None:
        """
        Send debug information about current conversation state (for development)
        
        Args:
            update: Telegram update object
            user_id: User ID
        """
        try:
            session = self.get_user_session_safely(user_id)
            if session:
                debug_info = MessageFormatter.format_session_summary(session)
                await self._safe_reply(update, f"🔧 Debug Info:\n{debug_info}")
            else:
                await self._safe_reply(update, "🔧 No session found")
        except Exception as e:
            self.logger.error(f"Failed to send debug info: {e}")


# Standalone command functions for use with CommandHandler
async def lunch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Standalone lunch command function
    
    Args:
        update: Telegram update object
        context: Bot context
        
    Returns:
        int: Next conversation state
    """
    storage_manager = context.bot_data.get('storage_manager')
    if not storage_manager:
        logger.error("Storage manager not found in bot_data")
        await update.message.reply_text("⚠️ Bot configuration error. Please try again later.")
        return ConversationHandler.END
    
    handler = MeetupHandler(storage_manager)
    return await handler.lunch_command(update, context)


async def study_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Standalone study command function
    
    Args:
        update: Telegram update object
        context: Bot context
        
    Returns:
        int: Next conversation state
    """
    storage_manager = context.bot_data.get('storage_manager')
    if not storage_manager:
        logger.error("Storage manager not found in bot_data")
        await update.message.reply_text("⚠️ Bot configuration error. Please try again later.")
        return ConversationHandler.END
    
    handler = MeetupHandler(storage_manager)
    return await handler.study_command(update, context)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Standalone cancel command function
    
    Args:
        update: Telegram update object
        context: Bot context
        
    Returns:
        int: ConversationHandler.END
    """
    storage_manager = context.bot_data.get('storage_manager')
    if not storage_manager:
        logger.error("Storage manager not found in bot_data")
        await update.message.reply_text("⚠️ Bot configuration error. Please try again later.")
        return ConversationHandler.END
    
    handler = MeetupHandler(storage_manager)
    return await handler.cancel_conversation(update, context)


async def location_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Standalone location callback function
    
    Args:
        update: Telegram update object
        context: Bot context
        
    Returns:
        int: Next conversation state
    """
    storage_manager = context.bot_data.get('storage_manager')
    if not storage_manager:
        logger.error("Storage manager not found in bot_data")
        if update.callback_query:
            await update.callback_query.answer("Configuration error")
            await update.callback_query.message.reply_text("⚠️ Bot configuration error. Please try again later.")
        return ConversationHandler.END
    
    handler = MeetupHandler(storage_manager)
    return await handler.location_callback(update, context)


async def time_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Standalone time input function
    
    Args:
        update: Telegram update object
        context: Bot context
        
    Returns:
        int: Next conversation state
    """
    storage_manager = context.bot_data.get('storage_manager')
    if not storage_manager:
        logger.error("Storage manager not found in bot_data")
        await update.message.reply_text("⚠️ Bot configuration error. Please try again later.")
        return ConversationHandler.END
    
    handler = MeetupHandler(storage_manager)
    return await handler.time_input(update, context)


async def time_skip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Standalone time skip callback function
    
    Args:
        update: Telegram update object
        context: Bot context
        
    Returns:
        int: Next conversation state
    """
    storage_manager = context.bot_data.get('storage_manager')
    if not storage_manager:
        logger.error("Storage manager not found in bot_data")
        if update.callback_query:
            await update.callback_query.answer("Configuration error")
            await update.callback_query.message.reply_text("⚠️ Bot configuration error. Please try again later.")
        return ConversationHandler.END
    
    handler = MeetupHandler(storage_manager)
    return await handler.time_skip_callback(update, context)


async def friends_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Standalone friends callback function
    
    Args:
        update: Telegram update object
        context: Bot context
        
    Returns:
        int: Next conversation state
    """
    storage_manager = context.bot_data.get('storage_manager')
    if not storage_manager:
        logger.error("Storage manager not found in bot_data")
        if update.callback_query:
            await update.callback_query.answer("Configuration error")
            await update.callback_query.message.reply_text("⚠️ Bot configuration error. Please try again later.")
        return ConversationHandler.END
    
    handler = MeetupHandler(storage_manager)
    return await handler.friends_callback(update, context)


async def confirm_invitation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Standalone confirmation callback function
    
    Args:
        update: Telegram update object
        context: Bot context
        
    Returns:
        int: ConversationHandler.END
    """
    storage_manager = context.bot_data.get('storage_manager')
    if not storage_manager:
        logger.error("Storage manager not found in bot_data")
        if update.callback_query:
            await update.callback_query.answer("Configuration error")
            await update.callback_query.message.reply_text("⚠️ Bot configuration error. Please try again later.")
        return ConversationHandler.END
    
    handler = MeetupHandler(storage_manager)
    return await handler.confirm_invitation(update, context)