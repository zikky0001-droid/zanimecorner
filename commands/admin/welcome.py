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
    
    # Get chat_id
    if update:
        chat = update.effective_chat
        chat_id = chat.id
        if chat.type == 'private':
            await update.message.reply_text("❌ This command can only be used in groups!")
            return
        
        async def reply(text):
            await update.message.reply_text(text, parse_mode='Markdown')
    else:
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
        
        if not reply:
            reply = lambda text: bot.send_message(chat_id, text, parse_mode='Markdown')
    
    from utils.database import Database
    db = Database()
    
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
        await reply(f"✅ Welcome message set:\n\n{msg}")
    else:
        await reply("❌ Invalid command. Use /welcome for help.")
        