"""
Message templates for UniLinkUp Telegram Bot
"""

# Welcome and Help Messages
WELCOME_MESSAGE = """
🎓 Welcome to UniLinkUp! 

I'm your friendly campus meetup organizer! 🤖✨

**What I can help you with:**
🍽️ `/lunch` - Grab lunch with friends
📚 `/study` - Organize study sessions  
📋 `/recent` - Check recent invitations
🆘 `/help` - Get help anytime

Ready to connect with your friends? Let's go! 🚀
"""

# Command Prompts
LUNCH_PROMPT = "🍽️ Awesome! Time for some good food and great company! 🍕\nWhere would you like to meet up?"
STUDY_PROMPT = "📚 Perfect! Let's get those study vibes going! 📖✨\nWhere should we hit the books together?"

TIME_PROMPT = """
⏰ When would you like to meet? 

You can specify a time (e.g., "2:30 PM", "in 30 minutes") or just press /skip to leave it flexible.
"""

FRIENDS_PROMPT = "👥 Time to gather the squad! 🎉\nWho would you like to invite? Tap to select your friends:"

CONFIRMATION_PROMPT = """
✅ Perfect! Here's your meetup summary:

📍 Location: {location}
⏰ Time: {time}
👥 Friends: {friends}

Ready to send invitations?
"""

# Notification Messages
INVITATION_NOTIFICATION = """
🔔 New {meetup_type} invitation from {organizer}!

📍 {location}
⏰ {time}
👥 Also invited: {other_friends}

Hope to see you there! 😊
"""

# Status Messages
NO_RECENT_PINGS = "📭 No recent invitations yet! 🤔\nTime to be the social butterfly! Use /lunch or /study to get started! 🦋✨"

RECENT_PINGS_HEADER = "📋 Recent Invitations:"

INVITATION_SENT = "🎉 Boom! Invitations sent! 📱✨\nYour friends have been notified and are probably already excited! 😊"

# Error Messages
ERROR_INVALID_TIME = "⚠️ Invalid time format. Please try again or use /skip."

ERROR_NO_FRIENDS_SELECTED = "⚠️ Please select at least one friend to invite."

ERROR_GENERAL = "😅 Oops! Something went wrong. Please try again."

ERROR_CONVERSATION_TIMEOUT = "⏱️ Session timed out. Please start over with a new command."

# Button Labels
BUTTON_CONFIRM = "✅ Send Invitations"
BUTTON_CANCEL = "❌ Cancel"
BUTTON_SKIP_TIME = "⏭️ Skip (Flexible Time)"