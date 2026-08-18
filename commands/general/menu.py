"""
Menu Command - Display full bot menu with interactive buttons
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
import os
import pathlib

from utils.command_loader import COMMANDS

COMMAND_NAME = 'menu'
ALIASES = ['help', 'commands']
DESCRIPTION = 'Display full bot menu with interactive buttons'
ADMIN_ONLY = False
OWNER_ONLY = False
GROUP_ONLY = False
BOT_ADMIN_NEEDED = False

# ============================================
# BOT IMAGE PATH
# ============================================
BOT_IMAGE_PATH = pathlib.Path(__file__).parent.parent.parent / 'utils' / 'bot_image.png'

def get_bot_image():
    """Get bot image bytes if exists"""
    try:
        if BOT_IMAGE_PATH.exists():
            with open(BOT_IMAGE_PATH, 'rb') as f:
                return f.read()
    except Exception:
        pass
    return None

# ============================================
# CATEGORY CONFIGURATION
# ============================================
CATEGORY_CONFIG = {
    'general': {'emoji': '📨', 'label': 'General Commands'},
    'admin': {'emoji': '🔧', 'label': 'Admin Commands'},
    'owner': {'emoji': '🔒', 'label': 'Owner Commands'},
    'utility': {'emoji': '🛠️', 'label': 'Utility Commands'},
    'media': {'emoji': '🎬', 'label': 'Media Commands'},
    'fun': {'emoji': '🎮', 'label': 'Fun Commands'},
    'ai': {'emoji': '🤖', 'label': 'AI Commands'}
}

# ============================================
# COMMAND LABEL MAP
# ============================================
COMMAND_LABELS = {
    'hi': '👋 Say Hello',
    'menu': '📋 Show Menu',
    'ping': '🏓 Ping',
    'active': '📊 Active Users',
    'inactive': '🔇 Inactive Users',
    'welcome': '👋 Welcome Message',
    'goodbye': '👋 Goodbye Message',
    'antilink': '🔗 Anti-Link',
    'restart': '🔄 Restart Bot',
    'stats': '📊 Bot Stats',
    'base64': '🔐 Base64',
    'password': '🔑 Password',
    'notes': '📝 Notes',
    'instagram': '📸 Instagram',
    'song': '🎵 Song',
    'video': '🎬 Video',
    'bomb': '💣 Bomb Game',
    'tictactoe': '❌⭕ TicTacToe',
    'qwen': '🧠 Qwen AI',
    'wormgpt': '🐛 WormGPT',
}

# ============================================
# SMALL CAPS FONT MAP
# ============================================
small_caps = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ',
    'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ',
    's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
    'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ',
    'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ',
    'S': 's', 'T': 'ᴛ', 'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
    '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒', '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗'
}

def to_small_caps(text):
    if not text:
        return ''
    return ''.join(small_caps.get(char, char) for char in str(text))

# ============================================
# GET COMMANDS FOR CATEGORY
# ============================================
def get_commands_for_category(category):
    commands = []
    for cmd_name, cmd_info in COMMANDS.items():
        if cmd_info.get('category') == category:
            label = COMMAND_LABELS.get(cmd_name, f"/{cmd_name}")
            commands.append({
                'name': cmd_name,
                'label': label,
                'admin_only': cmd_info.get('admin_only', False),
                'owner_only': cmd_info.get('owner_only', False),
            })
    commands.sort(key=lambda x: x['name'])
    return commands

# ============================================
# SEND MENU WITH IMAGE
# ============================================
async def send_menu_with_image(update_obj, context, text, reply_markup, is_callback=False):
    """Send menu with image"""
    image_bytes = get_bot_image()
    
    if is_callback:
        query = update_obj.callback_query
        if image_bytes:
            try:
                await query.edit_message_caption(
                    caption=text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"[MENU] Edit caption failed: {e}")
                await query.message.reply_photo(
                    photo=image_bytes,
                    caption=text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        else:
            await query.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    else:
        if image_bytes:
            await update_obj.message.reply_photo(
                photo=image_bytes,
                caption=text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update_obj.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

# ============================================
# SEND CATEGORY MENU
# ============================================
async def send_category_menu(update_obj, context, category_key):
    category_config = CATEGORY_CONFIG.get(category_key)
    if not category_config:
        return
    
    query = update_obj.callback_query
    await query.answer()
    
    bot_name = context.bot.username or 'DEV ZIKKY MD'
    
    commands = get_commands_for_category(category_key)
    
    if not commands:
        await query.edit_message_text(
            f"📭 No commands found in *{category_config['label']}*",
            parse_mode='Markdown'
        )
        return
    
    menu_text = f"""╭━༺ *{to_small_caps(category_config['label'])}* ༻━╮
┃ {category_config['emoji']} *{to_small_caps('COMMANDS')}* ({len(commands)})
┣━━━━━━━━━┫
┃ 💡 *{to_small_caps('TAP A BUTTON TO EXECUTE')}*
┃
╰━━━━━━━━━━━━━━━╯
*{to_small_caps('Powered by')} ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ*"""

    keyboard = []
    for cmd in commands:
        label = cmd['label']
        if cmd.get('owner_only'):
            label = f"👑 {label}"
        elif cmd.get('admin_only'):
            label = f"🛡️ {label}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"cmd_{cmd['name']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await send_menu_with_image(update_obj, context, menu_text, reply_markup, is_callback=True)

# ============================================
# SEND MAIN MENU (WITH IMAGE)
# ============================================
async def send_main_menu(update_obj, context, message=None):
    bot_name = context.bot.username or 'DEV ZIKKY MD'
    prefix = '/'
    total_commands = len(COMMANDS)
    
    menu_text = f"""╭━༺ *🔰 {to_small_caps('BOT MENU')} ❤️* ༻━╮
┃
┃ 🤖 *{to_small_caps('BOT NAME')}* : @{bot_name}
┃ ⚡ *{to_small_caps('PREFIX')}* : {prefix}
┃ 📊 *{to_small_caps('COMMANDS')}* : {total_commands}
┃
┣━━━━━━━━━┫
┃ 💡 *{to_small_caps('SELECT A CATEGORY BELOW')}*
┃
╰━━━━━━━━━━━━━━━╯
*{to_small_caps('Powered by')} ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ*"""

    keyboard = []
    for key, category in CATEGORY_CONFIG.items():
        count = len(get_commands_for_category(key))
        button_text = f"{category['emoji']} {category['label']} ({count})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"cat_{key}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if message:
        try:
            await message.edit_caption(
                caption=menu_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"[MENU] Edit caption failed: {e}")
            image_bytes = get_bot_image()
            if image_bytes:
                await message.reply_photo(
                    photo=image_bytes,
                    caption=menu_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                await message.reply_text(
                    menu_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
    else:
        await send_menu_with_image(update_obj, context, menu_text, reply_markup, is_callback=False)

# ============================================
# EXECUTE COMMAND FROM CALLBACK
# ============================================
async def execute_command_from_callback(query, command_name, context):
    """Execute a command directly from callback query"""
    from utils.command_loader import get_command
    
    cmd_info = get_command(command_name)
    if not cmd_info:
        await query.answer(f"❌ Command /{command_name} not found", show_alert=True)
        return
    
    cmd_func = cmd_info['function']
    
    # Create extra object
    extra = {
        'chat_id': query.message.chat.id,
        'user_id': query.from_user.id,
        'user_name': query.from_user.first_name,
        'chat_type': query.message.chat.type,
        'is_owner': False,
        'is_admin': False,
        'is_bot_admin': True,
        'reply': query.message.reply_text,
        'bot': context.bot,
        'update': None,
        'context': context,
        'react': None,
    }
    
    try:
        await cmd_func(None, context, [], extra)
        await query.answer(f"✅ /{command_name} executed!", show_alert=False)
    except Exception as e:
        print(f"[MENU] Error executing {command_name}: {e}")
        await query.answer(f"❌ Error: {str(e)[:50]}", show_alert=True)

# ============================================
# BUTTON CALLBACK HANDLER
# ============================================
async def button_callback(update_obj, context):
    query = update_obj.callback_query
    data = query.data
    
    print(f"[MENU] Button clicked: {data}")
    
    if data == "back_to_menu":
        await query.answer()
        await send_main_menu(update_obj, context, query.message)
        return
    
    if data.startswith("cat_"):
        category = data.replace("cat_", "")
        await send_category_menu(update_obj, context, category)
        return
    
    if data.startswith("cmd_"):
        command = data.replace("cmd_", "")
        await query.answer(f"⏳ Executing /{command}...")
        
        # Execute command directly
        await execute_command_from_callback(query, command, context)
        return

# ============================================
# MAIN EXECUTE FUNCTION
# ============================================
async def execute(update_obj, context, args=None, extra=None):
    if update_obj.callback_query:
        await button_callback(update_obj, context)
        return
    
    await send_main_menu(update_obj, context)
    