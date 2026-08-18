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
    import psutil
    
    # Bot uptime
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime = time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))
    except:
        uptime = "Unknown"
    
    # System stats
    try:
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
    
    await update.message.reply_text(message, parse_mode='Markdown')
    
    