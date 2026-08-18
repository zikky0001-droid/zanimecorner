"""
DEV ZIKKY TELEGRAM - Permission System
"""

from config import Config

def is_owner(user_id):
    """Check if user is in owners list"""
    return user_id in Config.OWNER_IDS

def is_admin_in_list(user_id):  # ← RENAMED from is_admin
    """Check if user is in admin list"""
    return user_id in Config.ADMIN_IDS

def is_owner_or_admin(user_id):
    """Check if user is owner or admin"""
    return is_owner(user_id) or is_admin_in_list(user_id)  # ← Updated

async def is_admin_in_group(update, user_id):
    """Check if user is group admin"""
    try:
        chat = update.effective_chat
        if chat.type == 'private':
            return False
        member = await chat.get_member(user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

async def is_admin(update, user_id):
    """Check if user is either admin in list or group admin"""
    if is_owner(user_id):
        return True
    if is_admin_in_list(user_id):  # ← Updated
        return True
    return await is_admin_in_group(update, user_id)

async def is_bot_admin(update):
    """Check if bot is admin in the group"""
    try:
        chat = update.effective_chat
        if chat.type == 'private':
            return True
        bot_id = update.get_bot().id
        member = await chat.get_member(bot_id)
        return member.status in ['administrator', 'creator']
    except:
        return False
        
        