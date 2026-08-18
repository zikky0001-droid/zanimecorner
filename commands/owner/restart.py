"""
Restart Command - Restart the bot
"""

import sys

COMMAND_NAME = 'restart'
ALIASES = []
DESCRIPTION = 'Restart the bot'
ADMIN_ONLY = False
OWNER_ONLY = True
GROUP_ONLY = False
BOT_ADMIN_NEEDED = False

async def execute(update, context, args, extra):
    """Restart the bot"""
    await update.message.reply_text("🔄 Restarting bot...")
    # For Pterodactyl, the panel will restart the process
    sys.exit(0)
       