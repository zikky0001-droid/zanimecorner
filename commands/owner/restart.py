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
    
    # ============================================
    # HANDLE BOTH DIRECT COMMAND AND MENU BUTTON
    # ============================================
    
    # Restart message with styled formatting
    restart_msg = """╭━༺ *RESTART* ༻━╮
┃
┃ 🔄 *RESTARTING BOT...*
┃
┃ 💠 *PLEASE WAIT A MOMENT*
┃ ✨ *THE BOT WILL COME BACK*
┃ 🔥 *ONLINE SHORTLY IN 30 SECS*
┃
╰━━━━━━━━━━━━━━━━╯
*ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ*"""
    
    if update:
        # Direct command
        await update.message.reply_text(restart_msg, parse_mode='Markdown')
    else:
        # From menu button
        reply_func = extra.get('reply')
        if reply_func:
            await reply_func(restart_msg)
        else:
            bot = extra.get('bot')
            chat_id = extra.get('chat_id')
            await bot.send_message(
                chat_id=chat_id,
                text=restart_msg,
                parse_mode='Markdown'
            )
    
    # Exit to trigger restart
    sys.exit(0)
        