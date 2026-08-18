"""
Password Command - Generate strong passwords
"""

import random
import string

COMMAND_NAME = 'password'
ALIASES = ['pass', 'pwd']
DESCRIPTION = 'Generate strong passwords'
ADMIN_ONLY = False
OWNER_ONLY = False
GROUP_ONLY = False
BOT_ADMIN_NEEDED = False

async def execute(update, context, args, extra):
    """Generate a strong password"""
    
    if update:
        async def reply(text):
            await update.message.reply_text(text, parse_mode='Markdown')
    else:
        reply = extra.get('reply')
        if not reply:
            bot = extra.get('bot')
            chat_id = extra.get('chat_id')
            reply = lambda text: bot.send_message(chat_id, text, parse_mode='Markdown')
    
    length = 16
    if args and args[0].isdigit():
        length = min(int(args[0]), 64)
        if length < 8:
            length = 8
    
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    password = ''.join(random.choice(chars) for _ in range(length))
    
    strength = "💪 Strong"
    if length < 12:
        strength = "⚠️ Medium"
    if length < 8:
        strength = "🔴 Weak"
    
    await reply(
        f"🔑 *Generated Password*\n\n"
        f"`{password}`\n\n"
        f"📏 *Length:* {length}\n"
        f"📊 *Strength:* {strength}\n\n"
        f"💡 *Tip:* Store this password securely!"
    )
    
    