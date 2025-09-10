"""
User session model for UniLinkUp Telegram Bot
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from config.constants import ConversationState


@dataclass
class UserSession:
    """
    Represents a user's current session state and meetup being organized
    """
    user_id: int
    username: Optional[str] = None
    current_state: Optional[ConversationState] = None
    
    # Current meetup being organized
    meetup_type: Optional[str] = None  # "lunch" or "study"
    location: Optional[str] = None
    time: Optional[str] = None
    selected_friends: List[str] = field(default_factory=list)
    
    # Session metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def reset_current_meetup(self) -> None:
        """
        Reset the current meetup data while preserving user info
        """
        self.current_state = None
        self.meetup_type = None
        self.location = None
        self.time = None
        self.selected_friends = []
        self.last_activity = datetime.now()
    
    def update_activity(self) -> None:
        """
        Update the last activity timestamp
        """
        self.last_activity = datetime.now()
    
    def set_meetup_type(self, meetup_type: str) -> None:
        """
        Set the meetup type and update activity
        
        Args:
            meetup_type: Type of meetup ("lunch" or "study")
        """
        self.meetup_type = meetup_type
        self.update_activity()
    
    def set_location(self, location: str) -> None:
        """
        Set the meetup location and update activity
        
        Args:
            location: Selected location for the meetup
        """
        self.location = location
        self.update_activity()
    
    def set_time(self, time: str) -> None:
        """
        Set the meetup time and update activity
        
        Args:
            time: Time for the meetup
        """
        self.time = time
        self.update_activity()
    
    def toggle_friend(self, friend_name: str) -> bool:
        """
        Toggle friend selection state
        
        Args:
            friend_name: Name of the friend to toggle
            
        Returns:
            bool: True if friend was added, False if removed
        """
        self.update_activity()
        
        if friend_name in self.selected_friends:
            self.selected_friends.remove(friend_name)
            return False
        else:
            self.selected_friends.append(friend_name)
            return True
    
    def is_friend_selected(self, friend_name: str) -> bool:
        """
        Check if a friend is currently selected
        
        Args:
            friend_name: Name of the friend to check
            
        Returns:
            bool: True if friend is selected
        """
        return friend_name in self.selected_friends
    
    def get_friends_display(self) -> str:
        """
        Get formatted string of selected friends for display
        
        Returns:
            str: Comma-separated list of selected friends
        """
        if not self.selected_friends:
            return "None selected"
        return ", ".join(self.selected_friends)
    
    def is_meetup_complete(self) -> bool:
        """
        Check if all required meetup information is provided
        
        Returns:
            bool: True if meetup can be confirmed
        """
        return (
            self.meetup_type is not None and
            self.location is not None and
            len(self.selected_friends) > 0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session to dictionary for serialization
        
        Returns:
            Dict[str, Any]: Session data as dictionary
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "current_state": self.current_state.value if self.current_state else None,
            "meetup_type": self.meetup_type,
            "location": self.location,
            "time": self.time,
            "selected_friends": self.selected_friends,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSession':
        """
        Create UserSession from dictionary
        
        Args:
            data: Dictionary containing session data
            
        Returns:
            UserSession: Reconstructed session object
        """
        session = cls(
            user_id=data["user_id"],
            username=data.get("username"),
            meetup_type=data.get("meetup_type"),
            location=data.get("location"),
            time=data.get("time"),
            selected_friends=data.get("selected_friends", [])
        )
        
        # Handle state conversion
        if data.get("current_state"):
            session.current_state = ConversationState(data["current_state"])
        
        # Handle datetime conversion
        if data.get("created_at"):
            session.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("last_activity"):
            session.last_activity = datetime.fromisoformat(data["last_activity"])
            
        return session