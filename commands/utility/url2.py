"""
DEV ZIKKY TELEGRAM - URL2 / ZTGP2 / GOFILE Command

Features:
- Reply to a Telegram file with /url2
- Aliases: /gofile2, /upload2, /download2
- Confirmation BEFORE transferring the Telegram file
- Uses ztgp2 + Teleproto/MTProto
- ztgp2 downloads the Telegram file
- ztgp2 uploads the file to Gofile
- Python bot never downloads the large file
- HTML formatting throughout
- Reliable Confirm / Cancel buttons
- File-size validation BEFORE transfer
- Safe escaping of dynamic content
- Supports large files through the ztgp2 service
"""

import html
import time

import aiohttp

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
)


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
    "Download and upload files using ztgp2 + Gofile"
)

ADMIN_ONLY = False
OWNER_ONLY = False
GROUP_ONLY = False
BOT_ADMIN_NEEDED = False


# ============================================================
# ZTGP2 CONFIGURATION
# ============================================================

# Directly configured here as requested.
ZTGP2_URL = "https://ztgp2.onrender.com"


TRANSFER_URL = (
    f"{ZTGP2_URL}/transfer"
)


# ============================================================
# CONSTANTS
# ============================================================

MAX_IMAGE_SIZE = (
    20 * 1024 * 1024
)

MAX_AUDIO_SIZE = (
    80 * 1024 * 1024
)

MAX_VIDEO_SIZE = (
    500 * 1024 * 1024
)

MAX_DOCUMENT_SIZE = (
    1000 * 1024 * 1024
)


# ============================================================
# CALLBACK DATA
# ============================================================

CONFIRM_CALLBACK = (
    "url2_confirm_upload"
)

CANCEL_CALLBACK = (
    "url2_cancel_upload"
)


# ============================================================
# HTTP TIMEOUT
# ============================================================

REQUEST_TIMEOUT = aiohttp.ClientTimeout(
    total=3600,
    connect=30,
    sock_connect=30,
    sock_read=3600,
)


# ============================================================
# HTML HELPERS
# ============================================================

def esc(value):
    """
    Safely escape dynamic values for Telegram HTML.
    """

    return html.escape(
        str(value or "")
    )


# ============================================================
# FILE SIZE
# ============================================================

def format_size(size_bytes):
    """
    Convert bytes into a readable file size.
    """

    if size_bytes is None:
        return "Unknown"

    try:
        size_bytes = int(size_bytes)
    except (
        TypeError,
        ValueError,
    ):
        return "Unknown"

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 ** 2:
        return (
            f"{size_bytes / 1024:.1f} KB"
        )

    if size_bytes < 1024 ** 3:
        return (
            f"{size_bytes / (1024 ** 2):.1f} MB"
        )

    return (
        f"{size_bytes / (1024 ** 3):.2f} GB"
    )


# ============================================================
# FILE TYPE
# ============================================================

def get_file_type(
    mime_type,
    file_name,
):
    """
    Determine the general file type.
    """

    mime_type = (
        mime_type or ""
    ).lower()

    file_name = (
        file_name or ""
    ).lower()

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    if mime_type.startswith("image/"):

        return (
            "🖼️ Image",
            MAX_IMAGE_SIZE,
        )

    image_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".bmp",
        ".tiff",
        ".tif",
    )

    if file_name.endswith(
        image_extensions
    ):

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

    audio_extensions = (
        ".mp3",
        ".m4a",
        ".aac",
        ".ogg",
        ".wav",
        ".flac",
        ".opus",
    )

    if file_name.endswith(
        audio_extensions
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

    video_extensions = (
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".webm",
        ".flv",
        ".3gp",
        ".m4v",
    )

    if file_name.endswith(
        video_extensions
    ):

        return (
            "🎬 Video",
            MAX_VIDEO_SIZE,
        )

    # --------------------------------------------------------
    # ANIMATION
    # --------------------------------------------------------

    if mime_type == "image/gif":

        return (
            "🎞️ Animation",
            MAX_IMAGE_SIZE,
        )

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    return (
        "📄 Document",
        MAX_DOCUMENT_SIZE,
    )


# ============================================================
# EXTRACT TELEGRAM MEDIA INFORMATION
# ============================================================

def extract_media_info(message):
    """
    Extract file metadata WITHOUT downloading the file.

    Returns:
        dict | None
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
            "file_size": media.file_size,
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
            "file_size": media.file_size,
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
            "file_size": media.file_size,
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
            "file_size": media.file_size,
        }

    # --------------------------------------------------------
    # PHOTO
    # --------------------------------------------------------

    if message.photo:

        photo = message.photo[-1]

        return {
            "file_type": "photo",
            "mime_type": "image/jpeg",
            "file_name": (
                "telegram_photo.jpg"
            ),
            "file_size": photo.file_size,
        }

    # --------------------------------------------------------
    # VOICE
    # --------------------------------------------------------

    if message.voice:

        media = message.voice

        return {
            "file_type": "voice",
            "mime_type": media.mime_type or "",
            "file_name": (
                "telegram_voice.ogg"
            ),
            "file_size": media.file_size,
        }

    # --------------------------------------------------------
    # VIDEO NOTE
    # --------------------------------------------------------

    if message.video_note:

        media = message.video_note

        return {
            "file_type": "video_note",
            "mime_type": "video/mp4",
            "file_name": (
                "telegram_video_note.mp4"
            ),
            "file_size": media.file_size,
        }

    return None


# ============================================================
# GET MEDIA LIMIT
# ============================================================

def get_media_limit(info):
    """
    Determine the application's maximum allowed size.
    """

    mime_type = info.get(
        "mime_type",
        "",
    )

    file_name = info.get(
        "file_name",
        "",
    )

    _, limit = get_file_type(
        mime_type,
        file_name,
    )

    return limit


# ============================================================
# CREATE CONFIRMATION
# ============================================================

def create_confirmation(
    info,
    limit,
):
    """
    Build confirmation message and buttons.
    """

    file_name = info.get(
        "file_name",
        "telegram_file",
    )

    file_size = info.get(
        "file_size",
    )

    mime_type = info.get(
        "mime_type",
        "",
    )

    file_type, _ = get_file_type(
        mime_type,
        file_name,
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Confirm",
                    callback_data=(
                        CONFIRM_CALLBACK
                    ),
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data=(
                        CANCEL_CALLBACK
                    ),
                ),
            ]
        ]
    )

    text = (
        "📤 <b>ZTGP2 FILE TRANSFER</b>\n"
        "\n"
        f"📁 <b>Name:</b> "
        f"<code>{esc(file_name)}</code>\n"
        f"📦 <b>Size:</b> "
        f"{esc(format_size(file_size))}\n"
        f"📄 <b>Type:</b> "
        f"{esc(file_type)}\n"
        "\n"
        "🌐 <b>Destination:</b> Gofile\n"
        "⚡ <b>Method:</b> MTProto → Gofile\n"
        "\n"
        "⚠️ <b>Ready to transfer this file?</b>"
    )

    return text, keyboard


# ============================================================
# /url2 COMMAND
# ============================================================

async def url2_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Handle /url2 and aliases.
    """

    message = (
        update.effective_message
    )

    if not message:
        return

    # --------------------------------------------------------
    # REQUIRE REPLY
    # --------------------------------------------------------

    replied = (
        message.reply_to_message
    )

    if not replied:

        await message.reply_text(
            "❌ <b>Reply to a Telegram file "
            "with /url2</b>",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # EXTRACT METADATA
    # --------------------------------------------------------

    info = extract_media_info(
        replied
    )

    if not info:

        await message.reply_text(
            "❌ <b>No supported file was found "
            "in the replied message.</b>\n\n"
            "Reply to a document, video, audio, "
            "photo, animation, voice or video note.",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # SIZE
    # --------------------------------------------------------

    file_size = info.get(
        "file_size"
    )

    limit = get_media_limit(
        info
    )

    if (
        file_size is not None
        and file_size > limit
    ):

        await message.reply_text(
            "❌ <b>File is too large.</b>\n\n"
            f"📦 File size: "
            f"<b>{esc(format_size(file_size))}</b>\n"
            f"📏 Allowed: "
            f"<b>{esc(format_size(limit))}</b>",
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
            "file_name"
        ),
        "file_size": file_size,
        "mime_type": info.get(
            "mime_type"
        ),
        "created": time.time(),
    }

    # --------------------------------------------------------
    # CONFIRMATION
    # --------------------------------------------------------

    text, keyboard = (
        create_confirmation(
            info,
            limit,
        )
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
    """
    Handle Confirm / Cancel buttons.
    """

    query = (
        update.callback_query
    )

    if not query:
        return

    await query.answer()

    data = query.data

    # ========================================================
    # CANCEL
    # ========================================================

    if data == CANCEL_CALLBACK:

        context.user_data.pop(
            "url2_transfer",
            None,
        )

        await query.edit_message_text(
            "❌ <b>Transfer cancelled.</b>",
            parse_mode="HTML",
        )

        return

    # ========================================================
    # CONFIRM
    # ========================================================

    if data != CONFIRM_CALLBACK:
        return

    transfer = context.user_data.get(
        "url2_transfer"
    )

    if not transfer:

        await query.edit_message_text(
            "❌ <b>Transfer request expired.</b>\n\n"
            "Please reply to the file again "
            "with /url2.",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # CHECK REQUEST AGE
    # --------------------------------------------------------

    created = transfer.get(
        "created",
        0,
    )

    if (
        time.time() - created
        > 15 * 60
    ):

        context.user_data.pop(
            "url2_transfer",
            None,
        )

        await query.edit_message_text(
            "⌛ <b>Transfer request expired.</b>\n\n"
            "Please run /url2 again.",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # UPDATE MESSAGE
    # --------------------------------------------------------

    file_name = transfer.get(
        "file_name",
        "telegram_file",
    )

    file_size = transfer.get(
        "file_size"
    )

    await query.edit_message_text(
        "⏳ <b>Transfer started...</b>\n\n"
        f"📁 <b>File:</b> "
        f"<code>{esc(file_name)}</code>\n"
        f"📦 <b>Size:</b> "
        f"{esc(format_size(file_size))}\n\n"
        "📡 Connecting to ztgp2...\n"
        "⬇️ Downloading through MTProto...\n"
        "⬆️ Uploading to Gofile...\n\n"
        "Please wait...",
        parse_mode="HTML",
    )

    # --------------------------------------------------------
    # PAYLOAD
    # --------------------------------------------------------

    payload = {
        "chat_id": transfer.get(
            "chat_id"
        ),
        "message_id": transfer.get(
            "message_id"
        ),
        "file_name": file_name,
    }

    # --------------------------------------------------------
    # ZTGP2 REQUEST
    # --------------------------------------------------------

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

                status = (
                    response.status
                )

        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        try:

            result = (
                __import__(
                    "json"
                ).loads(
                    response_text
                )
            )

        except Exception:

            result = {
                "success": False,
                "error": (
                    "ztgp2 returned invalid JSON"
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

            context.user_data.pop(
                "url2_transfer",
                None,
            )

            await query.edit_message_text(
                "❌ <b>Transfer failed.</b>\n\n"
                f"<code>{esc(error[:1000])}</code>",
                parse_mode="HTML",
            )

            return

        # ----------------------------------------------------
        # TRANSFER ERROR
        # ----------------------------------------------------

        if not result.get(
            "success"
        ):

            error = result.get(
                "error",
                "Unknown transfer error.",
            )

            context.user_data.pop(
                "url2_transfer",
                None,
            )

            await query.edit_message_text(
                "❌ <b>Transfer failed.</b>\n\n"
                f"<code>{esc(error[:1000])}</code>",
                parse_mode="HTML",
            )

            return

        # ----------------------------------------------------
        # URL
        # ----------------------------------------------------

        download_url = result.get(
            "url"
        )

        if not download_url:

            context.user_data.pop(
                "url2_transfer",
                None,
            )

            await query.edit_message_text(
                "❌ <b>Transfer completed but "
                "no Gofile URL was returned.</b>",
                parse_mode="HTML",
            )

            return

        # ----------------------------------------------------
        # RESULT INFORMATION
        # ----------------------------------------------------

        returned_name = result.get(
            "file_name",
            file_name,
        )

        returned_size = result.get(
            "size_human",
            format_size(
                file_size
            ),
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔗 Open File",
                        url=download_url,
                    )
                ]
            ]
        )

        await query.edit_message_text(
            "✅ <b>UPLOAD COMPLETE</b>\n\n"
            f"📁 <b>Name:</b> "
            f"<code>{esc(returned_name)}</code>\n"
            f"📦 <b>Size:</b> "
            f"<b>{esc(returned_size)}</b>\n"
            "\n"
            "☁️ <b>Host:</b> Gofile\n"
            "⚡ <b>Transfer:</b> ztgp2 / MTProto\n"
            "\n"
            f"🔗 <b>Download:</b>\n"
            f"{esc(download_url)}",
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

        context.user_data.pop(
            "url2_transfer",
            None,
        )

    # --------------------------------------------------------
    # CONNECTION ERROR
    # --------------------------------------------------------

    except aiohttp.ClientError as error:

        context.user_data.pop(
            "url2_transfer",
            None,
        )

        await query.edit_message_text(
            "❌ <b>Could not connect to ztgp2.</b>\n\n"
            f"<code>{esc(str(error)[:1000])}</code>",
            parse_mode="HTML",
        )

    # --------------------------------------------------------
    # TIMEOUT
    # --------------------------------------------------------

    except TimeoutError:

        context.user_data.pop(
            "url2_transfer",
            None,
        )

        await query.edit_message_text(
            "❌ <b>Transfer timed out.</b>\n\n"
            "The file may be too large or the "
            "transfer may have taken too long.",
            parse_mode="HTML",
        )

    # --------------------------------------------------------
    # UNKNOWN ERROR
    # --------------------------------------------------------

    except Exception as error:

        context.user_data.pop(
            "url2_transfer",
            None,
        )

        await query.edit_message_text(
            "❌ <b>Unexpected transfer error.</b>\n\n"
            f"<code>{esc(str(error)[:1000])}</code>",
            parse_mode="HTML",
        )


# ============================================================
# HANDLER EXPORTS
# ============================================================

def get_handlers():
    """
    Optional helper for command loaders that expect
    a handler list.
    """

    return {
        "command": url2_command,
        "callback": button_callback,
    }
    
    
    