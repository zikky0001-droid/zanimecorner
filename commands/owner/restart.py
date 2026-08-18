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
    
    # Check if owner (in both cases)
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
    
    restart_msg = """╭━━━༺ *RESTART* ༻━━━╮
┃
┃ 🔄 *RESTARTING BOT...*
┃
┃ 💠 *PLEASE WAIT A MOMENT*
┃ ✨ *THE BOT WILL COME BACK*
┃ 🔥 *ONLINE SHORTLY IN 30 SECS*
┃
╰━━━━━━━━━━━━━━━━╯
> *ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ*"""
    
    if update:
        await update.message.reply_text(restart_msg, parse_mode='Markdown')
    else:
        reply = extra.get('reply')
        if reply:
            await reply(restart_msg)
        else:
            bot = extra.get('bot')
            chat_id = extra.get('chat_id')
            await bot.send_message(chat_id, restart_msg, parse_mode='Markdown')
    
    sys.exit(0)
    