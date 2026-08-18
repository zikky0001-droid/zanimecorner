"""
Base64 Command - Encode or decode Base64 strings
"""

import base64

COMMAND_NAME = 'base64'
ALIASES = ['b64']
DESCRIPTION = 'Encode or decode Base64 strings'
ADMIN_ONLY = False
OWNER_ONLY = False
GROUP_ONLY = False
BOT_ADMIN_NEEDED = False

async def execute(update, context, args, extra):
    """Encode or decode Base64"""
    
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
            "🔐 *Base64 Tool*\n\n"
            "Usage:\n"
            "/base64 encode <text> - Encode to Base64\n"
            "/base64 decode <text> - Decode from Base64\n\n"
            "Example:\n"
            "/base64 encode Hello World"
        )
        return
    
    action = args[0].lower()
    
    if action == 'encode' and len(args) > 1:
        text = ' '.join(args[1:])
        encoded = base64.b64encode(text.encode()).decode()
        await reply(f"🔐 *Encoded:*\n`{encoded}`")
        
    elif action == 'decode' and len(args) > 1:
        text = args[1]
        try:
            decoded = base64.b64decode(text).decode()
            await reply(f"🔓 *Decoded:*\n`{decoded}`")
        except:
            await reply("❌ Invalid Base64 string!")
    
    else:
        await reply("❌ Invalid usage. Use /base64 for help.")
                