#!/usr/bin/env python3
"""
DEV ZIKKY TELEGRAM - Main Entry Point (Webhook Version)
For Render
"""

import sys
import os
import logging
import signal
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

logger = setup_logger()

def handle_shutdown(signum, frame):
    logger.info("🛑 Received shutdown signal. Stopping bot...")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def main():
    try:
        print("\n" + "="*50)
        print("🚀 Installing DEV ZIKKY TELEGRAM Bot...")
        print("="*50)
        
        config = Config()
        
        if not config.BOT_TOKEN or config.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            print("❌ ERROR: BOT_TOKEN not configured!")
            sys.exit(1)
        
        print(f"📦 Bot Name: {config.BOT_NAME}")
        print(f"⚡ Prefix: {config.PREFIX}")
        print(f"👑 Owner(s): {config.OWNER_IDS}")
        print("="*50 + "\n")
        
        commands = load_commands()
        print(f"✅ Loaded {len(commands)} commands\n")
        
        logger.info("🔄 Creating bot application...")
        application = ApplicationBuilder().token(config.BOT_TOKEN).build()
        
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.ALL, message_handler))
        
        print("\n" + "="*50)
        print("✅ Bot connected successfully!")
        print(f"🤖 Bot Name: {config.BOT_NAME}")
        print(f"⚡ Prefix: {config.PREFIX}")
        print("="*50)
        print("⚡⚡DEV ZIKKY TELEGRAM Bot is ready to receive messages 🔥💥🎉")
        print("="*50 + "\n")
        
        # ✅ Use webhook instead of polling
        port = int(os.environ.get('PORT', 10000))
        
        # ✅ FIX: Get the Render URL properly
        render_url = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
        if not render_url:
            # Fallback: Use the service name
            render_url = os.environ.get('RENDER_SERVICE_NAME', 'localhost')
            if render_url != 'localhost':
                render_url = f"{render_url}.onrender.com"
        
        webhook_url = f"https://{render_url}/{config.BOT_TOKEN}"
        
        logger.info(f"🚀 Starting webhook on port {port}")
        logger.info(f"🔗 Webhook URL: {webhook_url}")
        
        # Also print for visibility
        print(f"🌐 Webhook URL: {webhook_url}")
        
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=config.BOT_TOKEN,
            webhook_url=webhook_url,
            drop_pending_updates=True
        )
        
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
    
    
    
    