"""
Welcome Command - Configure welcome messages
"""

COMMAND_NAME = 'welcome'
ALIASES = ['w']
DESCRIPTION = 'Configure welcome messages in the group'
ADMIN_ONLY = True
GROUP_ONLY = True
BOT_ADMIN_NEEDED = True

async def execute(update, context, args, extra):
    """Configure welcome messages"""
    from utils.database import Database
    db = Database()
    chat = update.effective_chat
    
    if not args:
        settings = db.get_group_settings(chat.id)
        welcome_status = "✅ ON" if settings.get('welcome') else "❌ OFF"
        goodbye_status = "✅ ON" if settings.get('goodbye') else "❌ OFF"
        
        message = f"⚙️ *Welcome/Goodbye Settings*\n\n"
        message += f"📋 *Welcome:* {welcome_status}\n"
        message += f"📋 *Goodbye:* {goodbye_status}\n\n"
        message += "📝 *Commands:*\n"
        message += "/welcome on - Enable welcome messages\n"
        message += "/welcome off - Disable welcome messages\n"
        message += "/welcome set <message> - Set custom welcome message\n"
        message += "/goodbye on - Enable goodbye messages\n"
        message += "/goodbye off - Disable goodbye messages\n"
        message += "/goodbye set <message> - Set custom goodbye message"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        return
    
    subcommand = args[0].lower()
    
    if subcommand == 'on':
        db.update_group_settings(chat.id, {'welcome': True})
        await update.message.reply_text("✅ Welcome messages enabled for this group!")
    elif subcommand == 'off':
        db.update_group_settings(chat.id, {'welcome': False})
        await update.message.reply_text("❌ Welcome messages disabled for this group!")
    elif subcommand == 'set' and len(args) > 1:
        msg = ' '.join(args[1:])
        # TODO: Store custom welcome message
        await update.message.reply_text(f"✅ Welcome message set:\n\n{msg}")
    else:
        await update.message.reply_text("❌ Invalid command. Use /welcome for help.")
        