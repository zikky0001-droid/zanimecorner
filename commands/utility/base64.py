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
    if not args:
        await update.message.reply_text(
            "🔐 *Base64 Tool*\n\n"
            "Usage:\n"
            "/base64 encode <text> - Encode to Base64\n"
            "/base64 decode <text> - Decode from Base64\n\n"
            "Example:\n"
            "/base64 encode Hello World",
            parse_mode='Markdown'
        )
        return
    
    action = args[0].lower()
    
    if action == 'encode' and len(args) > 1:
        text = ' '.join(args[1:])
        encoded = base64.b64encode(text.encode()).decode()
        await update.message.reply_text(f"🔐 *Encoded:*\n`{encoded}`", parse_mode='Markdown')
        
    elif action == 'decode' and len(args) > 1:
        text = args[1]
        try:
            decoded = base64.b64decode(text).decode()
            await update.message.reply_text(f"🔓 *Decoded:*\n`{decoded}`", parse_mode='Markdown')
        except:
            await update.message.reply_text("❌ Invalid Base64 string!")
    
    else:
        await update.message.reply_text("❌ Invalid usage. Use /base64 for help.")
        