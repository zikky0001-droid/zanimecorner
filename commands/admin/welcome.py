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
    
    # ============================================
    # HANDLE BOTH DIRECT COMMAND AND MENU BUTTON
    # ============================================
    
    if update:
        # Direct command
        chat = update.effective_chat
        user = update.effective_user
        
        async def reply(text):
            await update.message.reply_text(text, parse_mode='Markdown')
    else:
        # From menu button
        reply_func = extra.get('reply')
        if reply_func:
            reply = reply_func
        else:
            bot = extra.get('bot')
            chat_id = extra.get('chat_id')
            async def reply(text):
                await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
    
    from utils.database import Database
    db = Database()
    chat_id = update.effective_chat.id if update else extra.get('chat_id')
    
    if not args:
        settings = db.get_group_settings(chat_id)
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
        
        await reply(message)
        return
    
    subcommand = args[0].lower()
    
    if subcommand == 'on':
        db.update_group_settings(chat_id, {'welcome': True})
        await reply("✅ Welcome messages enabled for this group!")
    elif subcommand == 'off':
        db.update_group_settings(chat_id, {'welcome': False})
        await reply("❌ Welcome messages disabled for this group!")
    elif subcommand == 'set' and len(args) > 1:
        msg = ' '.join(args[1:])
        # TODO: Store custom welcome message
        await reply(f"✅ Welcome message set:\n\n{msg}")
    else:
        await reply("❌ Invalid command. Use /welcome for help.")
        
        