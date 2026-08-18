"""
Stats Command - Show bot statistics
"""

import os
import time
from datetime import datetime

COMMAND_NAME = 'stats'
ALIASES = ['status']
DESCRIPTION = 'Show bot statistics'
ADMIN_ONLY = False
OWNER_ONLY = True
GROUP_ONLY = False
BOT_ADMIN_NEEDED = False

async def execute(update, context, args, extra):
    """Show bot statistics"""
    
    # Check if owner
    user_id = None
    if update:
        user_id = update.effective_user.id
    else:
        user_id = extra.get('user_id')
    
    from utils.permissions import is_owner
    if not is_owner(user_id):
        if update:
            await update.message.reply_text("👑 This command is only for the bot owner!")
        else:
            reply = extra.get('reply')
            if reply:
                await reply("👑 This command is only for the bot owner!")
            else:
                bot = extra.get('bot')
                chat_id = extra.get('chat_id')
                await bot.send_message(chat_id, "👑 This command is only for the bot owner!")
        return
    
    # Get reply function
    if update:
        async def reply(text):
            await update.message.reply_text(text, parse_mode='Markdown')
    else:
        reply = extra.get('reply')
        if not reply:
            bot = extra.get('bot')
            chat_id = extra.get('chat_id')
            reply = lambda text: bot.send_message(chat_id, text, parse_mode='Markdown')
    
    # Bot uptime
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime = time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))
    except:
        uptime = "Unknown"
    
    # System stats
    try:
        import psutil
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
    except:
        cpu = "N/A"
        memory = "N/A"
        disk = "N/A"
    
    message = f"📊 *Bot Statistics*\n\n"
    message += f"🤖 *Bot Name:* DEV ZIKKY TELEGRAM\n"
    message += f"⏱️ *Uptime:* {uptime}\n"
    message += f"📅 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    message += f"\n💻 *System Stats:*\n"
    message += f"⚡ *CPU:* {cpu}%\n"
    message += f"🧠 *Memory:* {memory.percent if memory != 'N/A' else 'N/A'}%\n"
    message += f"💾 *Disk:* {disk.percent if disk != 'N/A' else 'N/A'}%\n"
    
    await reply(message)
    