"""
Keyboard factory for UniLinkUp Telegram Bot
"""

from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config.constants import LOCATIONS, FRIENDS, CALLBACK_LOCATION, CALLBACK_FRIEND, CALLBACK_CONFIRM
from models.user_session import UserSession


class KeyboardFactory:
    """
    Factory class for creating inline keyboards for the bot
    """
    
    @staticmethod
    def create_location_keyboard() -> InlineKeyboardMarkup:
        """
        Create inline keyboard for location selection
        
        Returns:
            InlineKeyboardMarkup: Keyboard with location options
        """
        keyboard = []
        
        # Create buttons for each location (2 per row for better layout)
        for i in range(0, len(LOCATIONS), 2):
            row = []
            
            # First location in the row
            location = LOCATIONS[i]
            callback_data = f"{CALLBACK_LOCATION}{i}"
            row.append(InlineKeyboardButton(location, callback_data=callback_data))
            
            # Second location in the row (if exists)
            if i + 1 < len(LOCATIONS):
                location = LOCATIONS[i + 1]
                callback_data = f"{CALLBACK_LOCATION}{i + 1}"
                row.append(InlineKeyboardButton(location, callback_data=callback_data))
            
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_friends_keyboard(session: UserSession) -> InlineKeyboardMarkup:
        """
        Create inline keyboard for friends selection with current state
        
        Args:
            session: User session containing current friend selections
            
        Returns:
            InlineKeyboardMarkup: Keyboard with friend options and selection state
        """
        keyboard = []
        
        # Create buttons for each friend (2 per row)
        for i in range(0, len(FRIENDS), 2):
            row = []
            
            # First friend in the row
            friend = FRIENDS[i]
            is_selected = session.is_friend_selected(friend)
            button_text = f"✅ {friend}" if is_selected else f"⬜ {friend}"
            callback_data = f"{CALLBACK_FRIEND}{i}"
            row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
            
            # Second friend in the row (if exists)
            if i + 1 < len(FRIENDS):
                friend = FRIENDS[i + 1]
                is_selected = session.is_friend_selected(friend)
                button_text = f"✅ {friend}" if is_selected else f"⬜ {friend}"
                callback_data = f"{CALLBACK_FRIEND}{i + 1}"
                row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
            
            keyboard.append(row)
        
        # Add action buttons
        action_row = []
        
        # Only show confirm button if at least one friend is selected
        if len(session.selected_friends) > 0:
            action_row.append(
                InlineKeyboardButton("✅ Confirm Selection", callback_data=f"{CALLBACK_CONFIRM}yes")
            )
        
        action_row.append(
            InlineKeyboardButton("❌ Cancel", callback_data=f"{CALLBACK_CONFIRM}cancel")
        )
        
        keyboard.append(action_row)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_confirmation_keyboard() -> InlineKeyboardMarkup:
        """
        Create inline keyboard for final confirmation
        
        Returns:
            InlineKeyboardMarkup: Keyboard with confirm/cancel options
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ Send Invitations", callback_data=f"{CALLBACK_CONFIRM}send"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"{CALLBACK_CONFIRM}cancel")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_time_skip_keyboard() -> InlineKeyboardMarkup:
        """
        Create inline keyboard for time input with skip option
        
        Returns:
            InlineKeyboardMarkup: Keyboard with skip option
        """
        keyboard = [
            [
                InlineKeyboardButton("⏭️ Skip (Flexible Time)", callback_data="time_skip")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_location_by_index(index: int) -> Optional[str]:
        """
        Get location name by index
        
        Args:
            index: Index of the location in LOCATIONS list
            
        Returns:
            Optional[str]: Location name or None if index is invalid
        """
        if 0 <= index < len(LOCATIONS):
            return LOCATIONS[index]
        return None
    
    @staticmethod
    def get_friend_by_index(index: int) -> Optional[str]:
        """
        Get friend name by index
        
        Args:
            index: Index of the friend in FRIENDS list
            
        Returns:
            Optional[str]: Friend name or None if index is invalid
        """
        if 0 <= index < len(FRIENDS):
            return FRIENDS[index]
        return None
    
    @staticmethod
    def parse_callback_data(callback_data: str) -> tuple[str, Optional[str]]:
        """
        Parse callback data to extract action and parameter
        
        Args:
            callback_data: Callback data from button press
            
        Returns:
            tuple[str, Optional[str]]: (action_type, parameter)
        """
        if callback_data.startswith(CALLBACK_LOCATION):
            index_str = callback_data[len(CALLBACK_LOCATION):]
            return ("location", index_str)
        
        elif callback_data.startswith(CALLBACK_FRIEND):
            index_str = callback_data[len(CALLBACK_FRIEND):]
            return ("friend", index_str)
        
        elif callback_data.startswith(CALLBACK_CONFIRM):
            action = callback_data[len(CALLBACK_CONFIRM):]
            return ("confirm", action)
        
        elif callback_data == "time_skip":
            return ("time_skip", None)
        
        else:
            return ("unknown", callback_data)
    
    @staticmethod
    def create_custom_keyboard(buttons: List[List[tuple[str, str]]]) -> InlineKeyboardMarkup:
        """
        Create a custom inline keyboard from button specifications
        
        Args:
            buttons: List of rows, each row is a list of (text, callback_data) tuples
            
        Returns:
            InlineKeyboardMarkup: Custom keyboard
        """
        keyboard = []
        
        for row_spec in buttons:
            row = []
            for text, callback_data in row_spec:
                row.append(InlineKeyboardButton(text, callback_data=callback_data))
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_available_locations() -> List[str]:
        """
        Get list of all available locations
        
        Returns:
            List[str]: List of location names
        """
        return LOCATIONS.copy()
    
    @staticmethod
    def get_available_friends() -> List[str]:
        """
        Get list of all available friends
        
        Returns:
            List[str]: List of friend names
        """
        return FRIENDS.copy()