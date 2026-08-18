"""
Active Users Command - Show active users in group
"""

COMMAND_NAME = 'active'
ALIASES = ['act']
DESCRIPTION = 'Show active users in the group'
ADMIN_ONLY = True
GROUP_ONLY = True
BOT_ADMIN_NEEDED = False

async def execute(update, context, args, extra):
    """Show active users in the group"""
    
    # Check if called from menu button
    if not update:
        # From menu button - get chat_id from extra
        chat_id = extra.get('chat_id')
        bot = extra.get('bot')
        reply = extra.get('reply')
        
        # Get group chat
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
    
    # Direct command
    if update:
        chat = update.effective_chat
        if chat.type == 'private':
            await update.message.reply_text("❌ This command can only be used in groups!")
            return
        
        async def reply(text):
            await update.message.reply_text(text, parse_mode='Markdown')
    else:
        # From menu button
        if not reply:
            reply = lambda text: bot.send_message(chat_id, text, parse_mode='Markdown')
    
    # TODO: Implement actual active users logic from database
    message = "📊 *Active Users*\n\n"
    message += "⏱️ Last 5 minutes\n"
    message += "👥 5 users\n\n"
    message += "1. @user1 - 47 messages\n"
    message += "2. @user2 - 32 messages\n"
    message += "3. @user3 - 28 messages\n"
    message += "4. @user4 - 15 messages\n"
    message += "5. @user5 - 8 messages\n"
    
    await reply(message)
    
    