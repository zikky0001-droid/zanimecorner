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
    
    # ============================================
    # HANDLE BOTH DIRECT COMMAND AND MENU BUTTON
    # ============================================
    
    if update:
        # Direct command - from user typing /inactive
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
    # INACTIVE USERS LOGIC
    # ============================================
    
    # TODO: Implement actual inactive users logic from database
    # For now, demo response
    message = "🔇 *Inactive Users*\n\n"
    message += "⏱️ Inactive for 7+ days\n"
    message += "👥 3 users\n\n"
    message += "1. @user1 - 45 days inactive\n"
    message += "2. @user2 - 32 days inactive\n"
    message += "3. @user3 - 21 days inactive\n"
    
    await reply(message)
        