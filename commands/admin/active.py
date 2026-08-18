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
    
    # ============================================
    # HANDLE BOTH DIRECT COMMAND AND MENU BUTTON
    # ============================================
    
    if update:
        # Direct command - from user typing /active
        chat = update.effective_chat
        user = update.effective_user
        
        async def reply(text):
            await update.message.reply_text(text, parse_mode='Markdown')
    else:
        # From menu button - update is None
        chat_id = extra.get('chat_id')
        user_id = extra.get('user_id')
        user_name = extra.get('user_name', 'User')
        reply_func = extra.get('reply')
        
        if not reply_func:
            # Fallback: use bot to send message
            bot = extra.get('bot')
            chat_id = extra.get('chat_id')
            async def reply(text):
                await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
        else:
            reply = reply_func
    
    # ============================================
    # ACTIVE USERS LOGIC
    # ============================================
    
    # TODO: Implement actual active users logic from database
    # For now, demo response
    message = "📊 *Active Users*\n\n"
    message += "⏱️ Last 5 minutes\n"
    message += "👥 5 users\n\n"
    message += "1. @user1 - 47 messages\n"
    message += "2. @user2 - 32 messages\n"
    message += "3. @user3 - 28 messages\n"
    message += "4. @user4 - 15 messages\n"
    message += "5. @user5 - 8 messages\n"
    
    await reply(message)
    