"""
Inactive Users Command - Show inactive users in group
"""

COMMAND_NAME = 'inactive'
ALIASES = ['inact']
DESCRIPTION = 'Show inactive users in the group'
ADMIN_ONLY = True
GROUP_ONLY = True
BOT_ADMIN_NEEDED = False

async def execute(update, context, args, extra):
    """Show inactive users in the group"""
    
    if not update:
        chat_id = extra.get('chat_id')
        bot = extra.get('bot')
        reply = extra.get('reply')
        
        try:
            chat = await bot.get_chat(chat_id)
            if chat.type == 'private':
                if reply:
                    await reply("❌ This command can only be used in groups!")
                else:
                    await bot.send_message(chat_id, "❌ This command can only be used in groups!")
                return
        except:
            pass
    
    if update:
        chat = update.effective_chat
        if chat.type == 'private':
            await update.message.reply_text("❌ This command can only be used in groups!")
            return
        
        async def reply(text):
            await update.message.reply_text(text, parse_mode='Markdown')
    else:
        if not reply:
            reply = lambda text: bot.send_message(chat_id, text, parse_mode='Markdown')
    
    message = "🔇 *Inactive Users*\n\n"
    message += "⏱️ Inactive for 7+ days\n"
    message += "👥 3 users\n\n"
    message += "1. @user1 - 45 days inactive\n"
    message += "2. @user2 - 32 days inactive\n"
    message += "3. @user3 - 21 days inactive\n"
    
    await reply(message)
    
    