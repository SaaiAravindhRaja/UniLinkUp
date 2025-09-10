"""
Ping record model for UniLinkUp Telegram Bot
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class PingRecord:
    """
    Represents a meetup invitation (ping) sent to friends
    """
    organizer_id: int
    organizer_name: str
    meetup_type: str  # "lunch" or "study"
    location: str
    time: str
    invited_friends: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def format_for_display(self) -> str:
        """
        Format ping record for display in recent history
        
        Returns:
            str: Formatted string for display
        """
        # Format timestamp
        time_str = self.timestamp.strftime("%m/%d %H:%M")
        
        # Format meetup type with emoji
        type_emoji = "🍽️" if self.meetup_type == "lunch" else "📚"
        
        # Format friends list
        friends_str = ", ".join(self.invited_friends)
        if len(friends_str) > 30:
            friends_str = friends_str[:27] + "..."
        
        # Format time display
        time_display = self.time if self.time else "Flexible time"
        
        return (
            f"{type_emoji} {self.meetup_type.title()} - {self.location}\n"
            f"⏰ {time_display} | 👥 {friends_str}\n"
            f"📅 {time_str} by {self.organizer_name}"
        )
    
    def get_short_summary(self) -> str:
        """
        Get a short one-line summary of the ping
        
        Returns:
            str: Short summary string
        """
        type_emoji = "🍽️" if self.meetup_type == "lunch" else "📚"
        friends_count = len(self.invited_friends)
        time_str = self.timestamp.strftime("%m/%d")
        
        return (
            f"{type_emoji} {self.meetup_type.title()} at {self.location} "
            f"({friends_count} friends) - {time_str}"
        )
    
    def get_friends_except(self, exclude_friend: str) -> List[str]:
        """
        Get list of invited friends excluding a specific friend
        
        Args:
            exclude_friend: Friend name to exclude from the list
            
        Returns:
            List[str]: List of friends excluding the specified one
        """
        return [friend for friend in self.invited_friends if friend != exclude_friend]
    
    def get_other_friends_display(self, exclude_friend: str) -> str:
        """
        Get display string of other invited friends (excluding one)
        
        Args:
            exclude_friend: Friend name to exclude from display
            
        Returns:
            str: Comma-separated list of other friends
        """
        other_friends = self.get_friends_except(exclude_friend)
        
        if not other_friends:
            return "No other friends"
        elif len(other_friends) == 1:
            return other_friends[0]
        else:
            return ", ".join(other_friends)
    
    def matches_criteria(self, meetup_type: str = None, location: str = None) -> bool:
        """
        Check if ping matches given criteria
        
        Args:
            meetup_type: Optional meetup type to match
            location: Optional location to match
            
        Returns:
            bool: True if ping matches all provided criteria
        """
        if meetup_type and self.meetup_type != meetup_type:
            return False
        
        if location and self.location != location:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ping record to dictionary for serialization
        
        Returns:
            Dict[str, Any]: Ping data as dictionary
        """
        return {
            "organizer_id": self.organizer_id,
            "organizer_name": self.organizer_name,
            "meetup_type": self.meetup_type,
            "location": self.location,
            "time": self.time,
            "invited_friends": self.invited_friends,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PingRecord':
        """
        Create PingRecord from dictionary
        
        Args:
            data: Dictionary containing ping data
            
        Returns:
            PingRecord: Reconstructed ping record
        """
        ping = cls(
            organizer_id=data["organizer_id"],
            organizer_name=data["organizer_name"],
            meetup_type=data["meetup_type"],
            location=data["location"],
            time=data["time"],
            invited_friends=data["invited_friends"]
        )
        
        # Handle datetime conversion
        if data.get("timestamp"):
            ping.timestamp = datetime.fromisoformat(data["timestamp"])
            
        return ping
    
    def __str__(self) -> str:
        """String representation of ping record"""
        return self.get_short_summary()
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging"""
        return (
            f"PingRecord(organizer={self.organizer_name}, "
            f"type={self.meetup_type}, location={self.location}, "
            f"friends={len(self.invited_friends)}, "
            f"timestamp={self.timestamp.strftime('%Y-%m-%d %H:%M')})"
        )