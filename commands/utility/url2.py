"""
DEV ZIKKY TELEGRAM - URL2 / ZTGP2 / GOFILE

Features:
- Reply to a Telegram file with /url2
- Aliases: /gofile2, /upload2, /download2
- Confirmation before transfer
- ZTGP2 handles Telegram MTProto download
- ZTGP2 uploads to Gofile
- Python bot never downloads the large file
- Large-file friendly
- File-size validation before transfer
- HTML formatting
- Confirm / Cancel buttons
- Request expiration
- Safe escaping
"""

import html
import json
import time

import aiohttp

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes


# ============================================================
# COMMAND CONFIG
# ============================================================

COMMAND_NAME = "url2"

ALIASES = [
    "gofile2",
    "upload2",
    "download2",
]

DESCRIPTION = (
    "Transfer Telegram files through ZTGP2 and Gofile"
)

ADMIN_ONLY = False
OWNER_ONLY = False
GROUP_ONLY = False
BOT_ADMIN_NEEDED = False


# ============================================================
# ZTGP2 CONFIG
# ============================================================

# Intentionally kept directly in this file.
ZTGP2_URL = "https://ztgp2.onrender.com"

TRANSFER_URL = f"{ZTGP2_URL}/transfer"


# ============================================================
# FILE LIMITS
# ============================================================

MAX_IMAGE_SIZE = 20 * 1024 * 1024
MAX_AUDIO_SIZE = 80 * 1024 * 1024
MAX_VIDEO_SIZE = 500 * 1024 * 1024
MAX_DOCUMENT_SIZE = 1000 * 1024 * 1024


# ============================================================
# CALLBACK DATA
# ============================================================

CONFIRM_CALLBACK = "url2_confirm_upload"
CANCEL_CALLBACK = "url2_cancel_upload"


# ============================================================
# REQUEST TIMEOUT
# ============================================================

REQUEST_TIMEOUT = aiohttp.ClientTimeout(
    total=3600,
    connect=30,
    sock_connect=30,
    sock_read=3600,
)


# ============================================================
# HELPERS
# ============================================================

def esc(value):
    """Safely escape dynamic Telegram HTML."""

    return html.escape(
        str(value or "")
    )


def format_size(size_bytes):
    """Convert bytes to readable size."""

    if size_bytes is None:
        return "Unknown"

    try:
        size_bytes = int(size_bytes)
    except (TypeError, ValueError):
        return "Unknown"

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"

    if size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"

    return f"{size_bytes / (1024 ** 3):.2f} GB"


# ============================================================
# FILE TYPE
# ============================================================

def get_file_type(mime_type, file_name):
    """
    Return:
        (type_name, maximum_size)
    """

    mime_type = (
        mime_type or ""
    ).lower()

    file_name = (
        file_name or ""
    ).lower()

    # --------------------------------------------------------
    # ANIMATION
    # --------------------------------------------------------

    if mime_type == "image/gif":

        return (
            "🎞️ Animation",
            MAX_IMAGE_SIZE,
        )

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    if mime_type.startswith("image/"):

        return (
            "🖼️ Image",
            MAX_IMAGE_SIZE,
        )

    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".bmp",
        ".tiff",
        ".tif",
    }

    if file_name.endswith(
        tuple(image_extensions)
    ):

        if file_name.endswith(".gif"):

            return (
                "🎞️ Animation",
                MAX_IMAGE_SIZE,
            )

        return (
            "🖼️ Image",
            MAX_IMAGE_SIZE,
        )

    # --------------------------------------------------------
    # AUDIO
    # --------------------------------------------------------

    if mime_type.startswith("audio/"):

        return (
            "🎵 Audio",
            MAX_AUDIO_SIZE,
        )

    audio_extensions = {
        ".mp3",
        ".m4a",
        ".aac",
        ".ogg",
        ".wav",
        ".flac",
        ".opus",
    }

    if file_name.endswith(
        tuple(audio_extensions)
    ):

        return (
            "🎵 Audio",
            MAX_AUDIO_SIZE,
        )

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    if mime_type.startswith("video/"):

        return (
            "🎬 Video",
            MAX_VIDEO_SIZE,
        )

    video_extensions = {
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".webm",
        ".flv",
        ".3gp",
        ".m4v",
    }

    if file_name.endswith(
        tuple(video_extensions)
    ):

        return (
            "🎬 Video",
            MAX_VIDEO_SIZE,
        )

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    return (
        "📄 Document",
        MAX_DOCUMENT_SIZE,
    )


# ============================================================
# MEDIA EXTRACTION
# ============================================================

def extract_media_info(message):
    """
    Extract Telegram media metadata.

    IMPORTANT:
    This does NOT download anything.
    """

    if not message:
        return None

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    if message.document:

        media = message.document

        return {
            "file_type": "document",
            "mime_type": media.mime_type or "",
            "file_name": (
                media.file_name
                or "telegram_file"
            ),
            "file_size": media.file_size or 0,
        }

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    if message.video:

        media = message.video

        return {
            "file_type": "video",
            "mime_type": media.mime_type or "",
            "file_name": (
                media.file_name
                or "telegram_video.mp4"
            ),
            "file_size": media.file_size or 0,
        }

    # --------------------------------------------------------
    # AUDIO
    # --------------------------------------------------------

    if message.audio:

        media = message.audio

        return {
            "file_type": "audio",
            "mime_type": media.mime_type or "",
            "file_name": (
                media.file_name
                or "telegram_audio"
            ),
            "file_size": media.file_size or 0,
        }

    # --------------------------------------------------------
    # ANIMATION
    # --------------------------------------------------------

    if message.animation:

        media = message.animation

        return {
            "file_type": "animation",
            "mime_type": media.mime_type or "",
            "file_name": (
                media.file_name
                or "telegram_animation.gif"
            ),
            "file_size": media.file_size or 0,
        }

    # --------------------------------------------------------
    # PHOTO
    # --------------------------------------------------------

    if message.photo:

        media = message.photo[-1]

        return {
            "file_type": "photo",
            "mime_type": "image/jpeg",
            "file_name": "telegram_photo.jpg",
            "file_size": media.file_size or 0,
        }

    # --------------------------------------------------------
    # VOICE
    # --------------------------------------------------------

    if message.voice:

        media = message.voice

        return {
            "file_type": "voice",
            "mime_type": media.mime_type or "audio/ogg",
            "file_name": "telegram_voice.ogg",
            "file_size": media.file_size or 0,
        }

    # --------------------------------------------------------
    # VIDEO NOTE
    # --------------------------------------------------------

    if message.video_note:

        media = message.video_note

        return {
            "file_type": "video_note",
            "mime_type": "video/mp4",
            "file_name": "telegram_video_note.mp4",
            "file_size": media.file_size or 0,
        }

    # --------------------------------------------------------
    # STICKER
    # --------------------------------------------------------

    if message.sticker:

        media = message.sticker

        if getattr(
            media,
            "is_video",
            False,
        ):

            return {
                "file_type": "sticker",
                "mime_type": "video/webm",
                "file_name": "telegram_sticker.webm",
                "file_size": media.file_size or 0,
            }

        if getattr(
            media,
            "is_animated",
            False,
        ):

            return {
                "file_type": "sticker",
                "mime_type": "application/x-tgsticker",
                "file_name": "telegram_sticker.tgs",
                "file_size": media.file_size or 0,
            }

        return {
            "file_type": "sticker",
            "mime_type": "image/webp",
            "file_name": "telegram_sticker.webp",
            "file_size": media.file_size or 0,
        }

    return None


# ============================================================
# SIZE LIMIT
# ============================================================

def get_media_limit(info):
    """Return maximum allowed size."""

    _, limit = get_file_type(
        info.get("mime_type"),
        info.get("file_name"),
    )

    return limit


# ============================================================
# CONFIRMATION MESSAGE
# ============================================================

def create_confirmation(info):
    """Create confirmation message and keyboard."""

    file_name = info.get(
        "file_name",
        "telegram_file",
    )

    file_size = info.get(
        "file_size",
        0,
    )

    mime_type = info.get(
        "mime_type",
        "",
    )

    file_type, limit = get_file_type(
        mime_type,
        file_name,
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Confirm",
                    callback_data=CONFIRM_CALLBACK,
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data=CANCEL_CALLBACK,
                ),
            ]
        ]
    )

    text = (
        "╭━━━༺ <b>📤 ZTGP2 TRANSFER</b> ༻━━━╮\n"
        "┃\n"
        f"┃ 📄 <b>Name:</b> "
        f"<code>{esc(file_name)}</code>\n"
        f"┃ 📦 <b>Size:</b> "
        f"{esc(format_size(file_size))}\n"
        f"┃ 📁 <b>Type:</b> "
        f"{esc(file_type)}\n"
        "┃\n"
        "┃ 🌐 <b>Destination:</b> Gofile\n"
        "┃ ⚡ <b>Method:</b> MTProto → Gofile\n"
        "┃\n"
        "┃ ⚠️ <b>Ready to transfer?</b>\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n"
        "<blockquote>"
        "ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ"
        "</blockquote>"
    )

    return text, keyboard


# ============================================================
# /URL2 COMMAND
# ============================================================

async def url2_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle /url2 and aliases."""

    message = update.effective_message

    if not message:
        return

    replied = message.reply_to_message

    # --------------------------------------------------------
    # REQUIRE REPLY
    # --------------------------------------------------------

    if not replied:

        await message.reply_text(
            "❌ <b>Reply to a Telegram file "
            "with /url2</b>\n\n"
            "Aliases:\n"
            "• <code>/gofile2</code>\n"
            "• <code>/upload2</code>\n"
            "• <code>/download2</code>",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # EXTRACT
    # --------------------------------------------------------

    info = extract_media_info(
        replied
    )

    if not info:

        await message.reply_text(
            "❌ <b>Unsupported media.</b>\n\n"
            "Supported:\n"
            "• Documents\n"
            "• Videos\n"
            "• Audio\n"
            "• Photos\n"
            "• Animations\n"
            "• Voice\n"
            "• Video notes\n"
            "• Stickers",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # SIZE CHECK
    # --------------------------------------------------------

    file_size = info.get(
        "file_size",
        0,
    )

    limit = get_media_limit(
        info
    )

    if (
        file_size
        and file_size > limit
    ):

        await message.reply_text(
            "❌ <b>File is too large.</b>\n\n"
            f"📦 <b>Size:</b> "
            f"{esc(format_size(file_size))}\n"
            f"📏 <b>Maximum:</b> "
            f"{esc(format_size(limit))}",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # STORE REQUEST
    # --------------------------------------------------------

    context.user_data[
        "url2_transfer"
    ] = {
        "chat_id": replied.chat_id,
        "message_id": replied.message_id,
        "file_name": info.get(
            "file_name",
            "telegram_file",
        ),
        "file_size": file_size,
        "mime_type": info.get(
            "mime_type",
            "",
        ),
        "created": time.time(),
        "processing": False,
    }

    # --------------------------------------------------------
    # CONFIRM
    # --------------------------------------------------------

    text, keyboard = create_confirmation(
        info
    )

    await message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ============================================================
# CALLBACK HANDLER
# ============================================================

async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle URL2 confirmation buttons."""

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    # --------------------------------------------------------
    # ONLY HANDLE URL2 CALLBACKS
    # --------------------------------------------------------

    if data not in {
        CONFIRM_CALLBACK,
        CANCEL_CALLBACK,
    }:
        return

    try:
        await query.answer()
    except Exception:
        pass

    # ========================================================
    # CANCEL
    # ========================================================

    if data == CANCEL_CALLBACK:

        context.user_data.pop(
            "url2_transfer",
            None,
        )

        try:

            await query.edit_message_text(
                "❌ <b>Transfer cancelled.</b>",
                parse_mode="HTML",
            )

        except Exception as error:

            print(
                f"[URL2] Cancel error: {error}"
            )

        return

    # ========================================================
    # GET REQUEST
    # ========================================================

    transfer = context.user_data.get(
        "url2_transfer"
    )

    if not transfer:

        try:

            await query.edit_message_text(
                "⌛ <b>Transfer request expired.</b>\n\n"
                "Reply to the file with "
                "<code>/url2</code> again.",
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    # ========================================================
    # EXPIRATION
    # ========================================================

    created = transfer.get(
        "created",
        0,
    )

    if time.time() - created > 15 * 60:

        context.user_data.pop(
            "url2_transfer",
            None,
        )

        try:

            await query.edit_message_text(
                "⌛ <b>Transfer request expired.</b>\n\n"
                "Please run <code>/url2</code> again.",
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    # ========================================================
    # DOUBLE CLICK PROTECTION
    # ========================================================

    if transfer.get(
        "processing",
        False,
    ):

        try:

            await query.answer(
                "⏳ Transfer already processing..."
            )

        except Exception:
            pass

        return

    transfer["processing"] = True

    file_name = transfer.get(
        "file_name",
        "telegram_file",
    )

    file_size = transfer.get(
        "file_size",
        0,
    )

    # ========================================================
    # START MESSAGE
    # ========================================================

    try:

        await query.edit_message_text(
            "⏳ <b>ZTGP2 transfer started...</b>\n\n"
            f"📄 <b>File:</b> "
            f"<code>{esc(file_name)}</code>\n"
            f"📦 <b>Size:</b> "
            f"{esc(format_size(file_size))}\n\n"
            "📡 Connecting to ZTGP2...\n"
            "⚡ MTProto → Gofile\n\n"
            "Please wait...",
            parse_mode="HTML",
        )

    except Exception as error:

        print(
            f"[URL2] Progress message error: {error}"
        )

    # ========================================================
    # PAYLOAD
    # ========================================================

    payload = {
        "chat_id": transfer.get(
            "chat_id"
        ),
        "message_id": transfer.get(
            "message_id"
        ),
        "file_name": file_name,
    }

    # ========================================================
    # ZTGP2 TRANSFER
    # ========================================================

    try:

        async with aiohttp.ClientSession(
            timeout=REQUEST_TIMEOUT
        ) as session:

            async with session.post(
                TRANSFER_URL,
                json=payload,
            ) as response:

                response_text = (
                    await response.text()
                )

                status = response.status

        # ----------------------------------------------------
        # PARSE JSON
        # ----------------------------------------------------

        try:

            result = json.loads(
                response_text
            )

        except json.JSONDecodeError:

            result = {
                "success": False,
                "error": (
                    "ZTGP2 returned invalid JSON."
                ),
            }

        # ----------------------------------------------------
        # HTTP ERROR
        # ----------------------------------------------------

        if status != 200:

            error = result.get(
                "error",
                f"HTTP {status}",
            )

            await query.edit_message_text(
                "❌ <b>ZTGP2 transfer failed.</b>\n\n"
                f"<code>{esc(str(error)[:1000])}</code>",
                parse_mode="HTML",
            )

            return

        # ----------------------------------------------------
        # TRANSFER FAILURE
        # ----------------------------------------------------

        if not result.get(
            "success",
            False,
        ):

            error = result.get(
                "error",
                "Unknown ZTGP2 error.",
            )

            await query.edit_message_text(
                "❌ <b>Transfer failed.</b>\n\n"
                f"<code>{esc(str(error)[:1000])}</code>",
                parse_mode="HTML",
            )

            return

        # ----------------------------------------------------
        # GET URL
        # ----------------------------------------------------

        download_url = result.get(
            "url"
        )

        if not download_url:

            await query.edit_message_text(
                "❌ <b>Transfer completed, "
                "but no Gofile URL was returned.</b>",
                parse_mode="HTML",
            )

            return

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        returned_name = result.get(
            "file_name",
            file_name,
        )

        returned_size = result.get(
            "size_human",
            format_size(file_size),
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔗 Open Gofile",
                        url=download_url,
                    )
                ]
            ]
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        await query.edit_message_text(
            "╭━━━༺ "
            "<b>✅ UPLOAD COMPLETE</b> "
            "༻━━━╮\n"
            "┃\n"
            f"┃ 📄 <b>File:</b> "
            f"<code>{esc(returned_name)}</code>\n"
            f"┃ 📦 <b>Size:</b> "
            f"<b>{esc(returned_size)}</b>\n"
            "┃\n"
            "┃ ☁️ <b>Host:</b> Gofile\n"
            "┃ ⚡ <b>Transfer:</b> ZTGP2 / MTProto\n"
            "┃\n"
            "╰━━━━━━━━━━━━━━━━━━╯\n"
            "<blockquote>"
            "ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ"
            "</blockquote>",
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    # ========================================================
    # TIMEOUT
    # ========================================================

    except asyncio.TimeoutError:

        await query.edit_message_text(
            "❌ <b>ZTGP2 transfer timed out.</b>\n\n"
            "The transfer took too long.",
            parse_mode="HTML",
        )

    # ========================================================
    # CONNECTION ERROR
    # ========================================================

    except aiohttp.ClientError as error:

        await query.edit_message_text(
            "❌ <b>Could not connect to ZTGP2.</b>\n\n"
            f"<code>{esc(str(error)[:1000])}</code>",
            parse_mode="HTML",
        )

    # ========================================================
    # UNKNOWN ERROR
    # ========================================================

    except Exception as error:

        print(
            f"[URL2] Transfer error: {error}"
        )

        try:

            await query.edit_message_text(
                "❌ <b>Unexpected transfer error.</b>\n\n"
                f"<code>{esc(str(error)[:1000])}</code>",
                parse_mode="HTML",
            )

        except Exception:
            pass

    finally:

        context.user_data.pop(
            "url2_transfer",
            None,
        )


# ============================================================
# STANDARD COMMAND LOADER ENTRY POINT
# ============================================================

async def execute(
    update,
    context,
    args=None,
    extra=None,
):
    """
    Standard DEV ZIKKY command entry point.

    This is IMPORTANT because command_loader
    expects execute().
    """

    await url2_command(
        update,
        context,
    )


# ============================================================
# HANDLER EXPORT
# ============================================================

def get_handlers():
    """
    Optional compatibility helper.
    """

    return {
        "command": url2_command,
        "callback": button_callback,
    }


# ============================================================
# REGISTER HANDLERS
# ============================================================

def register_handlers(application):
    """
    Callback handling is done by the central router
    in main.py.

    No catch-all CallbackQueryHandler is registered here.
    """

    return
        
    