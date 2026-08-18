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
    chat = update.effective_chat
    
    # TODO: Implement inactive users logic
    # For now, simple response
    message = "🔇 *Inactive Users*\n\n"
    message += "⏱️ Inactive for 7+ days\n"
    message += "👥 3 users\n\n"
    message += "1. @user1 - 45 days inactive\n"
    message += "2. @user2 - 32 days inactive\n"
    message += "3. @user3 - 21 days inactive\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')
    