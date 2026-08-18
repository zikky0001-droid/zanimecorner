"""
DEV ZIKKY TELEGRAM - Message Handler
"""

import logging
import sys
import random
import traceback
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from utils.database import Database
from utils.command_loader import get_command
from utils.permissions import is_owner, is_admin, is_admin_in_group, is_bot_admin, is_owner_or_admin
from utils.logger import get_logger

logger = get_logger()
db = Database()

# ============================================
# REACTION HELPER (SILENT - NO LOGS)
# ============================================
async def add_reaction(update: Update, emoji: str):
    """Add reaction to a message silently"""
    try:
        message = update.message
        if not message:
            return
        
        # Check if method exists
        if not hasattr(message, 'set_reaction'):
            return
        
        # Try to set reaction
        await message.set_reaction([emoji])
        
    except Exception:
        # Silently fail - no logs
        pass

# ============================================
# REACTION SETS
# ============================================
REACTIONS = {
    'success': ['✅', '🎉', '✨', '🌟'],
    'error': ['❌', '💀', '⚠️', '😱'],
    'wait': ['⏳', '⌛', '⏰'],
    'command': ['⚡', '💫', '🎯', '🔥'],
    'welcome': ['👋', '🤗', '🎉', '🥳'],
    'goodbye': ['👋', '😢', '🥺'],
    'active': ['📊', '📈', '🔥'],
    'inactive': ['🔇', '💤', '😴'],
    'owner': ['👑', '🔒', '⚜️'],
    'admin': ['🛡️', '⚔️', '🔰'],
    'unknown': ['🤔', '😶‍🌫️', '❓', '😅', '🥴', '😂', '👻', '🙈', '💔', '🤦']
}

def get_random_reaction(category: str):
    """Get random reaction from category"""
    emojis = REACTIONS.get(category, ['🔹'])
    return random.choice(emojis)

# ============================================
# UNKNOWN COMMAND HANDLER
# ============================================
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands with reaction"""
    from config import Config
    message = update.message
    command_name = message.text.split()[0][1:] if message.text else ''
    
    # Strip @botusername if present
    if '@' in command_name:
        command_name = command_name.split('@')[0]
    
    # Add reaction before replying (silent)
    await add_reaction(update, get_random_reaction('unknown'))
    
    await message.reply_text(
        f"❌ Command *\"{command_name}\"* not found\n"
        f"💡 Use *{Config.PREFIX}menu* to see all commands\n"
        f"*ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ*",
        parse_mode='Markdown'
    )

# ============================================
# MAIN MESSAGE HANDLER
# ============================================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all incoming messages - Acts as command router"""
    try:
        # Skip edits and non-message updates
        if not update.message:
            return
        
        message = update.message
        chat = message.chat
        user = message.from_user
        config = Config()
        
        # Get message text
        text = message.text or message.caption or ''
        
        # Check if it's a command
        if not text.startswith(config.PREFIX):
            return
        
        # Parse command - REMOVE BOT USERNAME
        parts = text.split()
        raw_command = parts[0].lower()[1:]  # Remove '/'
        
        # ✅ FIX: Strip @botusername from command
        if '@' in raw_command:
            command_name = raw_command.split('@')[0]
        else:
            command_name = raw_command
        
        args = parts[1:] if len(parts) > 1 else []
        
        # Get user info
        user_id = user.id
        user_name = user.first_name or user.username or str(user_id)
        chat_id = chat.id
        chat_type = chat.type
        
        logger.info(f"📩 Command: {command_name} (raw: {raw_command}) | User: {user_name} ({user_id}) | Chat: {chat_id} ({chat_type})")
        
        # Add reaction for command (silent)
        await add_reaction(update, get_random_reaction('command'))
        
        # Permission checks
        is_user_owner = is_owner(user_id)
        is_user_admin = await is_admin(update, user_id)
        is_user_owner_or_admin = is_owner_or_admin(user_id)

        # ✅ FIXED: Renamed variable to avoid conflict with function name
        bot_is_admin = await is_bot_admin(update) if chat_type != 'private' else True

        # Get command
        cmd_info = get_command(command_name)
        if not cmd_info:
            await unknown_command(update, context)
            return

        cmd_func = cmd_info['function']

        # Permission validation
        if cmd_info.get('owner_only', False) and not is_user_owner:
            logger.warning(f"🚫 {user_name} attempted owner-only command: {command_name}")
            await add_reaction(update, get_random_reaction('owner'))
            await message.reply_text(config.MESSAGES['owner_only'])
            return

        if cmd_info.get('admin_only', False) and not is_user_owner_or_admin:
            logger.warning(f"🚫 {user_name} attempted admin-only command: {command_name}")
            await add_reaction(update, get_random_reaction('admin'))
            await message.reply_text(config.MESSAGES['admin_only'])
            return

        if cmd_info.get('group_only', False) and chat_type == 'private':
            await add_reaction(update, '👥')
            await message.reply_text(config.MESSAGES['group_only'])
            return

        if cmd_info.get('private_only', False) and chat_type != 'private':
            await add_reaction(update, '💬')
            await message.reply_text(config.MESSAGES['private_only'])
            return

        if cmd_info.get('bot_admin_needed', False) and not bot_is_admin:
            await add_reaction(update, '🤖')
            await message.reply_text(config.MESSAGES['bot_admin_needed'])
            return

        # Command execution
        try:
            # Send typing indicator
            await context.bot.send_chat_action(chat_id=chat_id, action='typing')
            
            # Execute command
            logger.info(f"✅ Executing command: {command_name} by {user_name}")
            
            # Create extra object
            extra = {
                'chat_id': chat_id,
                'user_id': user_id,
                'user_name': user_name,
                'chat_type': chat_type,
                'is_owner': is_user_owner,
                'is_admin': is_user_admin,
                'is_bot_admin': bot_is_admin,
                'reply': message.reply_text,
                'react': add_reaction,
                'update': update,
                'context': context,
                'bot': context.bot
            }
            
            await cmd_func(update, context, args, extra)
            
        except Exception as cmd_error:
            logger.error(f"❌ Command execution error: {cmd_error}")
            logger.error(traceback.format_exc())
            await add_reaction(update, get_random_reaction('error'))
            try:
                await message.reply_text(f"❌ Error executing command: {str(cmd_error)}")
            except Exception as reply_error:
                # If reply fails, send via bot directly
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Error executing command: {str(cmd_error)}"
                )
        
    except Exception as e:
        logger.error(f"❌ Error in message handler: {e}")
        logger.error(traceback.format_exc())
        try:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        except:
            pass

# ============================================
# GROUP PARTICIPANT UPDATE HANDLER
# ============================================
async def group_participant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle group participant updates (join/leave)"""
    try:
        chat = update.effective_chat
        user = update.effective_user
        new_chat_members = update.message.new_chat_members
        left_chat_member = update.message.left_chat_member
        
        # Get group settings
        group_settings = db.get_group_settings(chat.id)
        
        # Welcome message
        if new_chat_members and group_settings.get('welcome', False):
            for member in new_chat_members:
                if member.id == context.bot.id:
                    continue
                
                # Add welcome reaction (silent)
                await add_reaction(update, '👋')
                
                welcome_text = f"🎉 Welcome @{member.username or member.first_name} to {chat.title}!"
                await update.message.reply_text(welcome_text)
        
        # Goodbye message
        if left_chat_member and group_settings.get('goodbye', False):
            if left_chat_member.id != context.bot.id:
                # Add goodbye reaction (silent)
                await add_reaction(update, '👋')
                
                goodbye_text = f"👋 Goodbye @{left_chat_member.username or left_chat_member.first_name}! We'll miss you!"
                await update.message.reply_text(goodbye_text)
                
    except Exception as e:
        logger.error(f"❌ Group participant handler error: {e}")
        logger.error(traceback.format_exc())
        
        