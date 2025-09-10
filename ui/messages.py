"""
Message formatter for UniLinkUp Telegram Bot
"""

from typing import List, Optional
from datetime import datetime

from models.user_session import UserSession
from models.ping import PingRecord
from config.messages import *


class MessageFormatter:
    """
    Formats messages for display in the Telegram bot
    """
    
    @staticmethod
    def format_welcome_message(username: Optional[str] = None) -> str:
        """
        Format welcome message with optional personalization
        
        Args:
            username: Optional username for personalization
            
        Returns:
            str: Formatted welcome message
        """
        if username:
            personalized_welcome = f"🎓 Welcome to UniLinkUp, {username}!\n\n" + WELCOME_MESSAGE.split('\n', 1)[1]
            return personalized_welcome
        return WELCOME_MESSAGE
    
    @staticmethod
    def format_meetup_prompt(meetup_type: str) -> str:
        """
        Format initial meetup prompt based on type
        
        Args:
            meetup_type: Type of meetup ("lunch" or "study")
            
        Returns:
            str: Formatted prompt message
        """
        if meetup_type == "lunch":
            return LUNCH_PROMPT
        elif meetup_type == "study":
            return STUDY_PROMPT
        else:
            return f"Let's organize a {meetup_type} meetup! Where would you like to meet?"
    
    @staticmethod
    def format_time_prompt() -> str:
        """
        Format time input prompt
        
        Returns:
            str: Time prompt message
        """
        return TIME_PROMPT
    
    @staticmethod
    def format_friends_prompt(selected_count: int = 0) -> str:
        """
        Format friends selection prompt with current count
        
        Args:
            selected_count: Number of currently selected friends
            
        Returns:
            str: Friends selection prompt
        """
        if selected_count == 0:
            return FRIENDS_PROMPT
        else:
            return f"{FRIENDS_PROMPT}\n\n📊 Currently selected: {selected_count} friend{'s' if selected_count != 1 else ''}"
    
    @staticmethod
    def format_confirmation_message(session: UserSession) -> str:
        """
        Format confirmation message with meetup details
        
        Args:
            session: User session containing meetup details
            
        Returns:
            str: Formatted confirmation message
        """
        location = session.location or "Not specified"
        time = session.time or "Flexible time"
        friends = session.get_friends_display()
        
        return CONFIRMATION_PROMPT.format(
            location=location,
            time=time,
            friends=friends
        )
    
    @staticmethod
    def format_invitation_notification(ping: PingRecord, recipient_name: str) -> str:
        """
        Format invitation notification for a specific recipient
        
        Args:
            ping: Ping record containing invitation details
            recipient_name: Name of the recipient
            
        Returns:
            str: Formatted notification message
        """
        meetup_type = ping.meetup_type
        organizer = ping.organizer_name
        location = ping.location
        time = ping.time or "Flexible time"
        other_friends = ping.get_other_friends_display(recipient_name)
        
        return INVITATION_NOTIFICATION.format(
            meetup_type=meetup_type,
            organizer=organizer,
            location=location,
            time=time,
            other_friends=other_friends
        )
    
    @staticmethod
    def format_recent_pings(pings: List[PingRecord]) -> str:
        """
        Format recent pings for display
        
        Args:
            pings: List of recent ping records
            
        Returns:
            str: Formatted recent pings message
        """
        if not pings:
            return NO_RECENT_PINGS
        
        message_parts = [RECENT_PINGS_HEADER, ""]
        
        for i, ping in enumerate(pings, 1):
            formatted_ping = f"{i}. {ping.format_for_display()}"
            message_parts.append(formatted_ping)
            message_parts.append("")  # Empty line between pings
        
        # Remove the last empty line
        if message_parts[-1] == "":
            message_parts.pop()
        
        return "\n".join(message_parts)
    
    @staticmethod
    def format_invitation_sent_message(friends_count: int) -> str:
        """
        Format success message after sending invitations
        
        Args:
            friends_count: Number of friends invited
            
        Returns:
            str: Success message
        """
        if friends_count == 1:
            return "🎉 Invitation sent successfully! Your friend has been notified."
        else:
            return f"🎉 Invitations sent successfully! Your {friends_count} friends have been notified."
    
    @staticmethod
    def format_error_message(error_type: str, custom_message: str = None) -> str:
        """
        Format error message based on type
        
        Args:
            error_type: Type of error ("invalid_time", "no_friends", "general", "timeout")
            custom_message: Optional custom error message
            
        Returns:
            str: Formatted error message
        """
        if custom_message:
            return f"⚠️ {custom_message}"
        
        error_messages = {
            "invalid_time": ERROR_INVALID_TIME,
            "no_friends": ERROR_NO_FRIENDS_SELECTED,
            "general": ERROR_GENERAL,
            "timeout": ERROR_CONVERSATION_TIMEOUT
        }
        
        return error_messages.get(error_type, ERROR_GENERAL)
    
    @staticmethod
    def format_session_summary(session: UserSession) -> str:
        """
        Format current session summary for debugging or status
        
        Args:
            session: User session to summarize
            
        Returns:
            str: Session summary
        """
        parts = [
            f"👤 User: {session.username or 'Unknown'} (ID: {session.user_id})",
            f"🎯 Meetup Type: {session.meetup_type or 'Not set'}",
            f"📍 Location: {session.location or 'Not set'}",
            f"⏰ Time: {session.time or 'Not set'}",
            f"👥 Friends: {session.get_friends_display()}",
            f"🔄 State: {session.current_state.value if session.current_state else 'None'}"
        ]
        
        return "\n".join(parts)
    
    @staticmethod
    def format_ping_summary(ping: PingRecord) -> str:
        """
        Format ping record summary
        
        Args:
            ping: Ping record to summarize
            
        Returns:
            str: Ping summary
        """
        return ping.format_for_display()
    
    @staticmethod
    def format_help_message() -> str:
        """
        Format help message with available commands
        
        Returns:
            str: Help message
        """
        return """
🆘 **UniLinkUp Help**

**Available Commands:**
🍽️ `/lunch` - Organize a lunch meetup
📚 `/study` - Plan a study session
📋 `/recent` - View recent invitations
🆘 `/help` - Show this help message

**How it works:**
1. Choose a command to start organizing
2. Select a location from the options
3. Optionally set a time (or skip for flexible timing)
4. Select friends to invite
5. Confirm and send invitations!

**Tips:**
• You can cancel anytime by using the Cancel button
• Time is optional - skip it for flexible meetups
• Select multiple friends by tapping their names
• Recent invitations show the last 5 meetups

Need more help? Just start a new command and follow the prompts! 😊
        """.strip()
    
    @staticmethod
    def format_cancel_message() -> str:
        """
        Format cancellation message
        
        Returns:
            str: Cancellation message
        """
        return "❌ Meetup organization cancelled. Use /lunch or /study to start again!"
    
    @staticmethod
    def format_time_display(time_str: str) -> str:
        """
        Format time string for consistent display
        
        Args:
            time_str: Time string to format
            
        Returns:
            str: Formatted time string
        """
        if not time_str or time_str.strip() == "":
            return "Flexible time"
        return time_str.strip()
    
    @staticmethod
    def format_location_selected_message(location: str) -> str:
        """
        Format message when location is selected
        
        Args:
            location: Selected location
            
        Returns:
            str: Location confirmation message
        """
        return f"📍 Great choice! You selected: **{location}**\n\n{TIME_PROMPT}"
    
    @staticmethod
    def format_time_set_message(time: str) -> str:
        """
        Format message when time is set
        
        Args:
            time: Set time
            
        Returns:
            str: Time confirmation message
        """
        formatted_time = MessageFormatter.format_time_display(time)
        return f"⏰ Time set: **{formatted_time}**\n\n{FRIENDS_PROMPT}"
    
    @staticmethod
    def format_friends_updated_message(session: UserSession) -> str:
        """
        Format message when friends selection is updated
        
        Args:
            session: Current user session
            
        Returns:
            str: Friends update message
        """
        selected_count = len(session.selected_friends)
        
        if selected_count == 0:
            return "👥 No friends selected yet. Choose friends to invite:"
        else:
            friends_list = session.get_friends_display()
            return f"👥 Selected friends: **{friends_list}**\n\nSelect more friends or confirm your selection:"