import os
import aiohttp

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler


ZTGP2_URL = os.getenv(
    "ZTGP2_URL",
    "https://ztgp2.onrender.com"
).rstrip("/")


async def url2_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text(
            "❌ Reply to a Telegram file with /url2"
        )
        return

    replied = message.reply_to_message

    payload = {
        "chat_id": replied.chat_id,
        "message_id": replied.message_id,
    }

    # Use the Telegram message's filename when available
    if replied.document:
        payload["file_name"] = replied.document.file_name

    elif replied.video:
        payload["file_name"] = replied.video.file_name

    elif replied.audio:
        payload["file_name"] = replied.audio.file_name

    try:

        await message.reply_text(
            "⏳ Processing your file...\n"
            "Downloading → Gofile..."
        )

        async with aiohttp.ClientSession() as session:

            async with session.post(
                f"{ZTGP2_URL}/transfer",
                json=payload,
                timeout=aiohttp.ClientTimeout(
                    total=3600
                )
            ) as response:

                result = await response.json()

        if not result.get("success"):

            error = result.get(
                "error",
                "Transfer failed"
            )

            await message.reply_text(
                f"❌ Transfer failed:\n{error}"
            )

            return

        url = result.get("url")

        if not url:
            await message.reply_text(
                "❌ Gofile did not return a download URL."
            )
            return

        filename = result.get(
            "file_name",
            "file"
        )

        size = result.get(
            "size_human",
            "Unknown"
        )

        await message.reply_text(
            "✅ Upload complete!\n\n"
            f"📁 {filename}\n"
            f"📦 Size: {size}\n\n"
            f"🔗 {url}"
        )

    except Exception as error:

        await message.reply_text(
            "❌ Could not contact ztgp2:\n"
            f"{str(error)[:500]}"
        )


handler = CommandHandler(
    "url2",
    url2_command
)


