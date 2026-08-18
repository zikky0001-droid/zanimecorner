"""
DEV ZIKKY TELEGRAM - Configuration File
Hardcoded for Pterodactyl Panel
"""

# ============================================
# BOT CONFIGURATION
# ============================================

class Config:
    """Bot configuration - All values hardcoded here"""
    
    # ============================================
    # BOT TOKEN (REPLACE WITH YOUR TOKEN)
    # ============================================
    BOT_TOKEN = '8647876675:AAEc6Un7rt_hS2uXB6YtVOEFO2YgPHrRJnA' 
    
    # ============================================
    # BOT INFO
    # ============================================
    BOT_NAME = 'DEV ZIKKY TELEGRAM'
    BOT_VERSION = '1.0.0'
    PREFIX = '/'
    
    # ============================================
    # OWNERS (User IDs - replace with your IDs)
    # ============================================
    OWNER_IDS = [
        8025805233,  # ← CHANGE THIS - Your Telegram User ID
        # Add more owner IDs here
        # 987654321,  # Co-owner
        # 555555555   # Backup owner
    ]
    
    # ============================================
    # ADMINS (User IDs - replace with admin IDs)
    # ============================================
    ADMIN_IDS = [
        # Add admin user IDs here
        # 111111111,  # Admin 1
        # 222222222,  # Admin 2
        # 333333333   # Admin 3
    ]
    
    # ============================================
    # DATABASE SETTINGS
    # ============================================
    DATABASE_PATH = './database'
    
    # ============================================
    # API KEYS (Add your keys here)
    # ============================================
    OPENAI_API_KEY = ''  # Add your OpenAI key for ChatGPT
    NVIDIA_API_KEY = ''  # Add your NVIDIA key
    GOOGLE_API_KEY = ''  # Add your Google API key
    
    # ============================================
    # DEFAULT GROUP SETTINGS
    # ============================================
    DEFAULT_GROUP_SETTINGS = {
        'antilink': False,
        'antispam': False,
        'welcome': False,
        'goodbye': False,
        'slowmode': 0,
        'nsfw': False
    }
    
    # ============================================
    # MESSAGES
    # ============================================
    MESSAGES = {
        'owner_only': '👑 This command is only for the bot owner!',
        'admin_only': '🛡️ This command is only for group admins!',
        'group_only': '👥 This command can only be used in groups!',
        'private_only': '💬 This command can only be used in private chat!',
        'error': '❌ An error occurred! Please try again.',
        'wait': '⏳ Please wait...',
        'success': '✅ Success!',
        'bot_admin_needed': '🤖 Bot needs to be admin to execute this command!'
    }
    
    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL = 'INFO'
    LOG_FILE = './logs/bot.log'
    
    
    