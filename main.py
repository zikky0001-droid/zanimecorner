#!/usr/bin/env python3
"""
DEV ZIKKY TELEGRAM - Main Entry Point (Webhook Version)
For Render

Features:
- Webhook support for Render
- Central callback routing
- URL / Gofile Confirm + Cancel buttons
- Menu callback support
- Command/message handling
"""

import sys
import os
import logging
import signal
from pathlib import Path

# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# TELEGRAM
# ============================================================

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)


# ============================================================
# PROJECT IMPORTS
# ============================================================

from config import Config
from handler import message_handler, unknown_command
from utils.command_loader import load_commands
from utils.logger import setup_logger

# General menu callback
from commands.general.menu import button_callback as menu_button_callback

# URL / Gofile callback
from commands.utility.url import button_callback as url_button_callback


# ============================================================
# LOGGER
# ============================================================

logger = setup_logger()


# ============================================================
# CALLBACK NAMES
# ============================================================

# These MUST match url.py exactly.

URL_CONFIRM_CALLBACK = "url_confirm_upload"
URL_CANCEL_CALLBACK = "url_cancel_upload"


# ============================================================
# SHUTDOWN
# ============================================================

def handle_shutdown(signum, frame):
    logger.info(
        "🛑 Received shutdown signal. Stopping bot..."
    )

    sys.exit(0)


signal.signal(
    signal.SIGINT,
    handle_shutdown
)

signal.signal(
    signal.SIGTERM,
    handle_shutdown
)


# ============================================================
# CENTRAL CALLBACK ROUTER
# ============================================================

async def callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Central callback router.

    URL buttons are handled first.
    Everything else goes to the normal menu callback.
    """

    query = update.callback_query

    if not query:
        return

    callback_data = query.data or ""

    logger.info(
        f"🔘 Callback received: {callback_data}"
    )

    # ========================================================
    # URL / GOFILE BUTTONS
    # ========================================================

    if callback_data in {
        URL_CONFIRM_CALLBACK,
        URL_CANCEL_CALLBACK,
    }:

        logger.info(
            f"📦 Routing URL callback: {callback_data}"
        )

        try:

            await url_button_callback(
                update,
                context
            )

        except Exception as error:

            logger.exception(
                f"❌ URL callback error: {error}"
            )

            # Try to notify the user if the callback
            # handler itself failed.

            try:
                await query.answer(
                    "❌ An error occurred.",
                    show_alert=True
                )
            except Exception:
                pass

        return

    # ========================================================
    # OTHER BUTTONS
    # ========================================================

    try:

        await menu_button_callback(
            update,
            context
        )

    except Exception as error:

        logger.exception(
            f"❌ Menu callback error: {error}"
        )

        try:
            await query.answer(
                "❌ Button error.",
                show_alert=True
            )
        except Exception:
            pass


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        print("\n" + "=" * 50)
        print(
            "🚀 Installing DEV ZIKKY TELEGRAM Bot..."
        )
        print("=" * 50)

        # ====================================================
        # CONFIG
        # ====================================================

        config = Config()

        if (
            not config.BOT_TOKEN
            or config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE"
        ):

            print(
                "❌ ERROR: BOT_TOKEN not configured!"
            )

            sys.exit(1)

        print(
            f"📦 Bot Name: {config.BOT_NAME}"
        )

        print(
            f"⚡ Prefix: {config.PREFIX}"
        )

        print(
            f"👑 Owner(s): {config.OWNER_IDS}"
        )

        print("=" * 50 + "\n")


        # ====================================================
        # LOAD COMMANDS
        # ====================================================

        commands = load_commands()

        print(
            f"✅ Loaded {len(commands)} commands\n"
        )


        # ====================================================
        # CREATE APPLICATION
        # ====================================================

        logger.info(
            "🔄 Creating bot application..."
        )

        application = (
            ApplicationBuilder()
            .token(config.BOT_TOKEN)
            .build()
        )


        # ====================================================
        # CALLBACK HANDLER
        # ====================================================
        #
        # IMPORTANT:
        #
        # There is ONE central callback handler.
        #
        # callback_router decides whether the callback
        # belongs to URL/Gofile or the menu.
        #
        # This prevents the menu callback from stealing
        # the URL buttons.
        #
        # ====================================================

        application.add_handler(
            CallbackQueryHandler(
                callback_router
            )
        )


        # ====================================================
        # MESSAGE HANDLER
        # ====================================================

        application.add_handler(
            MessageHandler(
                filters.ALL,
                message_handler
            )
        )


        # ====================================================
        # BOT READY
        # ====================================================

        print("\n" + "=" * 50)

        print(
            "✅ Bot connected successfully!"
        )

        print(
            f"🤖 Bot Name: {config.BOT_NAME}"
        )

        print(
            f"⚡ Prefix: {config.PREFIX}"
        )

        print("=" * 50)

        print(
            "⚡⚡DEV ZIKKY TELEGRAM Bot "
            "is ready to receive messages 🔥💥🎉"
        )

        print("=" * 50 + "\n")


        # ====================================================
        # RENDER WEBHOOK
        # ====================================================

        port = int(
            os.environ.get(
                "PORT",
                10000
            )
        )


        # ====================================================
        # GET RENDER HOSTNAME
        # ====================================================

        render_url = os.environ.get(
            "RENDER_EXTERNAL_HOSTNAME"
        )

        if not render_url:

            render_url = os.environ.get(
                "RENDER_SERVICE_NAME",
                "localhost"
            )

            if render_url != "localhost":

                render_url = (
                    f"{render_url}.onrender.com"
                )


        # ====================================================
        # WEBHOOK URL
        # ====================================================

        webhook_url = (
            f"https://{render_url}/"
            f"{config.BOT_TOKEN}"
        )


        logger.info(
            f"🚀 Starting webhook on port {port}"
        )

        logger.info(
            f"🔗 Webhook URL: {webhook_url}"
        )

        print(
            f"🌐 Webhook URL: {webhook_url}"
        )


        # ====================================================
        # START WEBHOOK
        # ====================================================

        application.run_webhook(

            listen="0.0.0.0",

            port=port,

            url_path=config.BOT_TOKEN,

            webhook_url=webhook_url,

            drop_pending_updates=True
        )


    # ========================================================
    # SHUTDOWN
    # ========================================================

    except KeyboardInterrupt:

        logger.info(
            "🛑 Bot stopped by user"
        )

        print(
            "\n🛑 Bot stopped by user"
        )


    # ========================================================
    # FATAL ERROR
    # ========================================================

    except Exception as error:

        logger.exception(
            f"❌ Failed to start bot: {error}"
        )

        print(
            f"❌ Error: {error}"
        )

        sys.exit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
        
    
    