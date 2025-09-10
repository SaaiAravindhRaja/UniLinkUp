# UniLinkUp Telegram Bot 🎓

A Telegram bot to help university students organize meetups with friends for lunch and study sessions.

## Features ✨

- 🍽️ **Lunch Meetups** - Organize lunch gatherings with friends
- 📚 **Study Sessions** - Plan group study sessions  
- 📍 **Location Selection** - Choose from predefined campus locations
- ⏰ **Flexible Timing** - Set specific times or keep it flexible
- 👥 **Friend Selection** - Invite multiple friends with easy selection
- 📋 **Recent History** - View recent invitations and meetups
- 🔔 **Notifications** - Simulated friend notifications (for demo)

## Quick Start 🚀

### Prerequisites

- Python 3.8+
- A Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd unilinkup-telegram-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your bot token
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## Configuration ⚙️

### Environment Variables

Create a `.env` file or set these environment variables:

- `TELEGRAM_BOT_TOKEN` - Your bot token from BotFather (required)
- `LOG_LEVEL` - Logging level (default: INFO)
- `DEBUG` - Enable debug mode (default: false)

### Getting a Bot Token

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow the instructions
3. Choose a name and username for your bot
4. Copy the token and add it to your `.env` file

## Usage 📱

### Available Commands

- `/start` - Welcome message and bot introduction
- `/help` - Show help and available commands
- `/lunch` - Start organizing a lunch meetup
- `/study` - Start organizing a study session
- `/recent` - View recent invitations
- `/cancel` - Cancel current conversation

### How to Organize a Meetup

1. **Start** - Use `/lunch` or `/study`
2. **Location** - Select from campus locations
3. **Time** - Set a time or skip for flexible timing
4. **Friends** - Select friends to invite
5. **Confirm** - Review and send invitations

### Example Flow

```
User: /lunch
Bot: 🍽️ Great! Let's organize a lunch meetup. Where would you like to meet?
     [Campus Café] [Student Union] [Food Court] ...

User: [Selects Campus Café]
Bot: 📍 Great choice! You selected: Campus Café
     ⏰ When would you like to meet? (or skip for flexible time)

User: 12:30 PM
Bot: ⏰ Time set: 12:30 PM
     👥 Who would you like to invite? Select your friends:
     [Alex] [Sam] [Jordan] ...

User: [Selects Alex and Sam]
Bot: ✅ Perfect! Here's your meetup summary:
     📍 Location: Campus Café
     ⏰ Time: 12:30 PM  
     👥 Friends: Alex, Sam
     Ready to send invitations?

User: [Send Invitations]
Bot: 🎉 Invitations sent successfully! Your friends have been notified.
```

## Project Structure 📁

```
unilinkup-telegram-bot/
├── main.py                 # Bot entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .env.example           # Environment variables template
├── config/                # Configuration modules
│   ├── constants.py       # Bot constants and enums
│   ├── messages.py        # Message templates
│   └── settings.py        # Settings and validation
├── handlers/              # Command and callback handlers
│   ├── base.py           # Base handler class
│   ├── start.py          # Start/help commands
│   ├── meetup.py         # Meetup organization
│   ├── recent.py         # Recent pings display
│   └── error.py          # Global error handling
├── models/               # Data models
│   ├── user_session.py   # User session state
│   └── ping.py           # Meetup invitation records
├── storage/              # Data storage
│   └── manager.py        # Storage management
├── ui/                   # User interface components
│   ├── keyboards.py      # Inline keyboard factory
│   └── messages.py       # Message formatting
└── tests/                # Unit tests
    └── ...
```

## Development 🛠️

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

The project follows Python best practices:
- Type hints for better code clarity
- Comprehensive error handling
- Modular architecture
- Extensive logging

### Adding New Features

1. **Locations** - Edit `LOCATIONS` in `config/constants.py`
2. **Friends** - Edit `FRIENDS` in `config/constants.py`  
3. **Messages** - Update templates in `config/messages.py`
4. **Commands** - Add handlers in appropriate handler files

## Architecture 🏗️

### Key Components

- **Handlers** - Process user commands and callbacks
- **Models** - Data structures for sessions and pings
- **Storage** - In-memory storage with optional persistence
- **UI** - Keyboard and message formatting
- **Config** - Constants, messages, and settings

### Conversation Flow

The bot uses Telegram's ConversationHandler for multi-step interactions:

1. **LOCATION** - User selects meetup location
2. **TIME** - User sets time or skips
3. **FRIENDS** - User selects friends to invite
4. **CONFIRM** - User confirms and sends invitations

### Error Handling

- Global error handler catches all exceptions
- Graceful degradation for network issues
- Session cleanup on errors
- User-friendly error messages

## Deployment 🚀

### Local Development

```bash
python main.py
```

### Production Deployment

1. **Set environment variables**
2. **Use a process manager** (systemd, supervisor, etc.)
3. **Set up logging** to files
4. **Monitor** bot health and errors

### Docker (Optional)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## Troubleshooting 🔧

### Common Issues

1. **Bot not responding**
   - Check bot token is correct
   - Verify bot is not already running
   - Check network connectivity

2. **Permission errors**
   - Ensure bot has message permissions
   - Check if bot was blocked by user

3. **Configuration errors**
   - Verify environment variables
   - Check .env file format

### Logs

The bot logs important events and errors. Check console output or log files for debugging information.

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License 📄

This project is open source. See LICENSE file for details.

## Support 💬

For questions or issues:
- Check the troubleshooting section
- Review the logs for error messages
- Open an issue on the repository

---

**Happy organizing! 🎉**