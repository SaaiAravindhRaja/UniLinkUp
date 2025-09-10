# UniLinkUp Bot - Quick Start Guide 🚀

Get your UniLinkUp Telegram bot running in 5 minutes!

## Step 1: Get Your Bot Token 🤖

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Choose a name: `UniLinkUp Campus Bot`
4. Choose a username: `your_unilinkup_bot` (must end with 'bot')
5. Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 2: Set Up the Bot 💻

```bash
# Clone and enter directory
git clone <your-repo>
cd unilinkup-telegram-bot

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env file and add your token
nano .env
```

In `.env` file:
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
LOG_LEVEL=INFO
DEBUG=false
```

## Step 3: Run the Bot 🎯

```bash
python main.py
```

You should see:
```
INFO - UniLinkUp bot is ready! Starting polling...
```

## Step 4: Test Your Bot 🧪

1. Find your bot on Telegram (search for the username you created)
2. Send `/start`
3. Try organizing a meetup with `/lunch`

## That's it! 🎉

Your bot is now running and ready to help students organize meetups!

## Quick Commands Reference

- `/start` - Welcome message
- `/lunch` - Organize lunch meetup
- `/study` - Plan study session
- `/recent` - View recent invitations
- `/help` - Show help
- `/cancel` - Cancel current action

## Troubleshooting 🔧

**Bot not responding?**
- Check your token is correct
- Make sure bot is running (`python main.py`)
- Check console for error messages

**Permission errors?**
- Ensure bot can send messages
- Check if you accidentally blocked the bot

**Need help?**
- Check the full README.md
- Look at console logs for errors
- Verify your .env file format

## Next Steps 📈

- Customize locations in `config/constants.py`
- Modify friend names in `config/constants.py`
- Deploy to a server for 24/7 operation
- Add more features!

Happy organizing! 🎓✨