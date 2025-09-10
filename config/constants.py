"""
Configuration constants for UniLinkUp Telegram Bot
"""

import os
from enum import Enum
from typing import List

# Bot Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Conversation States
class ConversationState(Enum):
    LOCATION = "location"
    TIME = "time"
    FRIENDS = "friends"
    CONFIRM = "confirm"

# Predefined Locations
LOCATIONS: List[str] = [
    "📚 Main Library",
    "☕ Campus Café", 
    "🍕 Student Union",
    "🏫 Study Hall A",
    "🌳 Campus Quad",
    "🏃 Recreation Center",
    "🍔 Food Court",
    "🔬 Science Building"
]

# Predefined Friends List
FRIENDS: List[str] = [
    "Alex",
    "Sam", 
    "Jordan",
    "Casey",
    "Taylor",
    "Morgan",
    "Riley",
    "Avery"
]

# Callback Data Prefixes
CALLBACK_LOCATION = "loc_"
CALLBACK_FRIEND = "friend_"
CALLBACK_CONFIRM = "confirm_"

# Limits and Settings
MAX_RECENT_PINGS = 5
MAX_PING_HISTORY = 100