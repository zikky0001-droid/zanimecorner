#!/usr/bin/env python3
"""
DEV ZIKKY TELEGRAM - Main Entry Point
For Render / Pterodactyl Panel
"""

import sys
import os
import logging
import signal
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from handler import message_handler, unknown_command
from utils.command_loader import load_commands
from utils.logger import setup_logger

from commands.general.menu import button_callback

# ============================================
# SETUP LOGGING
# ============================================
logger = setup_logger()

# ============================================
# GRACEFUL SHUTDOWN HANDLER
# ============================================
def handle_shutdown(signum, frame):
    """Handle graceful shutdown"""
    logger.info("🛑 Received shutdown signal. Stopping bot...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# ============================================
# START WEB SERVER FOR RENDER
# ============================================
async def start_web_server():
    """Start a simple web server to keep Render alive"""
    try:
        from aiohttp import web
        
        async def health_check(request):
            return web.Response(text="Bot is running!", status=200)
        
        async def index(request):
            return web.Response(text="DEV ZIKKY TELEGRAM BOT", status=200)
        
        app = web.Application()
        app.router.add_get('/', index)
        app.router.add_get('/health', health_check)
        
        # Get port from environment or use 10000
        port = int(os.environ.get('PORT', 10000))
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"🌐 Web server started on port {port}")
        print(f"🌐 Web server started on port {port}")
        
        # Keep the server running
        while True:
            await asyncio.sleep(60)
            
    except ImportError:
        logger.warning("⚠️ aiohttp not installed. Web server not started.")
        print("⚠️ aiohttp not installed. Web server not started.")
        
        # Keep running without web server
        while True:
            await asyncio.sleep(60)

# ============================================
# MAIN FUNCTION
# ============================================
def main():
    """Start the bot"""
    try:
        print("\n" + "="*50)
        print("🚀 Installing DEV ZIKKY TELEGRAM Bot...")
        print("="*50)
        
        # Load configuration
        config = Config()
        
        # Validate bot token
        if not config.BOT_TOKEN or config.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            print("❌ ERROR: BOT_TOKEN not configured in config.py!")
            print("   Please add your Telegram Bot Token from @BotFather")
            sys.exit(1)
        
        print(f"📦 Bot Name: {config.BOT_NAME}")
        print(f"⚡ Prefix: {config.PREFIX}")
        print(f"👑 Owner(s): {config.OWNER_IDS}")
        print(f"📂 Database: {config.DATABASE_PATH}")
        print("="*50 + "\n")
        
        # Load commands
        commands = load_commands()
        print(f"✅ Loaded {len(commands)} commands\n")
        
        # ============================================
        # CREATE APPLICATION
        # ============================================
        logger.info("🔄 Creating bot application...")
        application = ApplicationBuilder().token(config.BOT_TOKEN).build()
        
        # ============================================
        # REGISTER HANDLERS
        # ============================================
        
        # ✅ Register CALLBACK QUERY HANDLER for menu buttons
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # ✅ Register message handler
        application.add_handler(MessageHandler(filters.ALL, message_handler))
        
        # ============================================
        # START THE BOT (WITH CONFLICT FIX)
        # ============================================
        print("\n" + "="*50)
        print("✅ Bot connected successfully!")
        print(f"🤖 Bot Name: {config.BOT_NAME}")
        print(f"⚡ Prefix: {config.PREFIX}")
        print(f"👑 Owners: {config.OWNER_IDS}")
        print(f"🛡️ Admins: {config.ADMIN_IDS if config.ADMIN_IDS else 'None set'}")
        print("="*50)
        print("⚡⚡DEV ZIKKY TELEGRAM Bot is ready to receive messages 🔥💥🎉")
        print("="*50 + "\n")
        
        # ✅ FIX: Run bot and web server concurrently
        async def run_bot():
            # Start the bot
            await application.initialize()
            await application.start()
            
            # Start polling
            await application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query', 'my_chat_member']
            )
            
            logger.info("🚀 Bot polling started!")
            print("🚀 Bot polling started!")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
        
        # Run both the bot and web server
        loop = asyncio.get_event_loop()
        
        # Start web server in background
        asyncio.create_task(start_web_server())
        
        # Run the bot
        loop.run_until_complete(run_bot())
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
        print("\n🛑 Bot stopped by user")
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
    
    
    
    
    
    