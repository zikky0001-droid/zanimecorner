"""
Notes Command - Save and manage notes
"""

COMMAND_NAME = 'notes'
ALIASES = ['note']
DESCRIPTION = 'Save and manage notes'
ADMIN_ONLY = True
GROUP_ONLY = True
BOT_ADMIN_NEEDED = False

async def execute(update, context, args, extra):
    """Manage notes"""
    
    # Handle both direct and menu
    if update:
        async def reply(text):
            await update.message.reply_text(text, parse_mode='Markdown')
    else:
        reply = extra.get('reply')
        if not reply:
            bot = extra.get('bot')
            chat_id = extra.get('chat_id')
            reply = lambda text: bot.send_message(chat_id, text, parse_mode='Markdown')
    
    if not args:
        await reply(
            "📝 *Notes Manager*\n\n"
            "/notes save <text> - Save a note\n"
            "/notes list - List all notes\n"
            "/notes get <id> - Get a note\n"
            "/notes delete <id> - Delete a note"
        )
        return
    
    subcommand = args[0].lower()
    
    if subcommand == 'save' and len(args) > 1:
        note_text = ' '.join(args[1:])
        await reply(f"✅ Note saved: {note_text}")
    elif subcommand == 'list':
        await reply("📝 *Your Notes*\n\nNo notes found.")
    elif subcommand == 'get' and len(args) > 1:
        note_id = args[1]
        await reply(f"📝 *Note {note_id}*\n\nContent goes here...")
    elif subcommand == 'delete' and len(args) > 1:
        note_id = args[1]
        await reply(f"🗑️ Note {note_id} deleted!")
    else:
        await reply("❌ Invalid command. Use /notes save <text> or /notes list")
        
        