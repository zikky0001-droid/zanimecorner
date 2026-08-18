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
    chat = update.effective_chat
    
    # TODO: Implement active users logic
    # For now, simple response
    message = "📊 *Active Users*\n\n"
    message += "⏱️ Last 5 minutes\n"
    message += "👥 5 users\n\n"
    message += "1. @user1 - 47 messages\n"
    message += "2. @user2 - 32 messages\n"
    message += "3. @user3 - 28 messages\n"
    message += "4. @user4 - 15 messages\n"
    message += "5. @user5 - 8 messages\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')
    