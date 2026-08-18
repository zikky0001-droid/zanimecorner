"""
DEV ZIKKY TELEGRAM - URL / GOFILE Command

Features:
- Reply to a Telegram file with /url
- Confirmation BEFORE downloading the file
- Async Telegram download + Gofile upload
- HTML formatting throughout
- Reliable Confirm / Cancel buttons
- Temporary-file cleanup
"""

import html
import json
import time
from pathlib import Path

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


COMMAND_NAME = "url"
ALIASES = ["gofile", "upload", "download"]
DESCRIPTION = "Download and upload files using Gofile API"

ADMIN_ONLY = False
OWNER_ONLY = False
GROUP_ONLY = False
BOT_ADMIN_NEEDED = False


# ============================================================
# CONSTANTS
# ============================================================

MAX_IMAGE_SIZE = 20 * 1024 * 1024
MAX_AUDIO_SIZE = 80 * 1024 * 1024
MAX_VIDEO_SIZE = 500 * 1024 * 1024
MAX_DOCUMENT_SIZE = 1000 * 1024 * 1024

GOFILE_UPLOAD_URL = "https://upload.gofile.io/uploadfile"

TEMP_DIR = Path(__file__).parent.parent.parent / "tmp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


# These MUST be different from your menu callbacks.
CONFIRM_CALLBACK = "url_confirm_upload"
CANCEL_CALLBACK = "url_cancel_upload"


# ============================================================
# HTML HELPER
# ============================================================

def esc(value):
    """Escape dynamic text for Telegram HTML."""
    return html.escape(str(value or ""))


# ============================================================
# FORMAT FILE SIZE
# ============================================================

def format_size(size_bytes):
    if not size_bytes:
        return "Unknown"

    size_bytes = int(size_bytes)

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"

    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# ============================================================
# FILE TYPE
# ============================================================

def get_file_type(mime_type, file_name):
    mime_type = (mime_type or "").lower()
    file_name = (file_name or "").lower()

    if mime_type.startswith("image/"):
        return "image"

    if mime_type.startswith("audio/"):
        return "audio"

    if mime_type.startswith("video/"):
        return "video"

    extension = Path(file_name).suffix.lower()

    if extension in {
        ".jpg", ".jpeg", ".png", ".gif",
        ".webp", ".bmp", ".svg"
    }:
        return "image"

    if extension in {
        ".mp3", ".wav", ".ogg",
        ".aac", ".flac", ".m4a"
    }:
        return "audio"

    if extension in {
        ".mp4", ".mov", ".avi",
        ".webm", ".mkv", ".mpeg"
    }:
        return "video"

    return "document"


def get_max_size(file_type):
    return {
        "image": MAX_IMAGE_SIZE,
        "audio": MAX_AUDIO_SIZE,
        "video": MAX_VIDEO_SIZE,
        "document": MAX_DOCUMENT_SIZE,
    }.get(file_type, MAX_DOCUMENT_SIZE)


def file_type_label(file_type, sticker=False, animated=False):

    if sticker:
        if animated:
            return "🎨 Animated Sticker"
        return "🎨 Static Sticker"

    return {
        "image": "🖼️ Image",
        "audio": "🎵 Audio",
        "video": "🎬 Video",
        "document": "📄 Document",
    }.get(file_type, "📁 File")


# ============================================================
# STICKER DETECTION
# ============================================================

def is_animated_sticker(sticker):
    return bool(
        getattr(sticker, "is_animated", False)
        or getattr(sticker, "is_video", False)
        or getattr(sticker, "mime_type", "")
        in {"video/webm", "video/mp4"}
    )


# ============================================================
# EXTRACT FILE INFORMATION
# ============================================================

def extract_file_info(message):
    """
    IMPORTANT:

    This function ONLY reads Telegram metadata.

    It does NOT call bot.get_file().
    It does NOT download anything.

    Download happens only after the user presses Confirm Upload.
    """

    # DOCUMENT
    if message.document:
        item = message.document

        name = item.file_name or "document"

        return {
            "file_id": item.file_id,
            "file_type": get_file_type(
                item.mime_type,
                name
            ),
            "file_size": item.file_size or 0,
            "file_name": name,
            "mime_type": item.mime_type,
            "sticker": False,
            "animated": False,
        }

    # PHOTO
    if message.photo:
        item = message.photo[-1]

        return {
            "file_id": item.file_id,
            "file_type": "image",
            "file_size": item.file_size or 0,
            "file_name": f"image_{int(time.time())}.jpg",
            "mime_type": "image/jpeg",
            "sticker": False,
            "animated": False,
        }

    # VIDEO
    if message.video:
        item = message.video

        return {
            "file_id": item.file_id,
            "file_type": "video",
            "file_size": item.file_size or 0,
            "file_name": (
                item.file_name
                or f"video_{int(time.time())}.mp4"
            ),
            "mime_type": item.mime_type or "video/mp4",
            "sticker": False,
            "animated": False,
        }

    # AUDIO
    if message.audio:
        item = message.audio

        return {
            "file_id": item.file_id,
            "file_type": "audio",
            "file_size": item.file_size or 0,
            "file_name": (
                item.file_name
                or f"audio_{int(time.time())}.mp3"
            ),
            "mime_type": item.mime_type or "audio/mpeg",
            "sticker": False,
            "animated": False,
        }

    # VOICE
    if message.voice:
        item = message.voice

        return {
            "file_id": item.file_id,
            "file_type": "audio",
            "file_size": item.file_size or 0,
            "file_name": f"voice_{int(time.time())}.ogg",
            "mime_type": "audio/ogg",
            "sticker": False,
            "animated": False,
        }

    # VIDEO NOTE
    if message.video_note:
        item = message.video_note

        return {
            "file_id": item.file_id,
            "file_type": "video",
            "file_size": item.file_size or 0,
            "file_name": (
                f"video_note_{int(time.time())}.mp4"
            ),
            "mime_type": "video/mp4",
            "sticker": False,
            "animated": False,
        }

    # STICKER
    if message.sticker:
        item = message.sticker

        animated = is_animated_sticker(item)

        return {
            "file_id": item.file_id,
            "file_type": "video" if animated else "image",
            "file_size": item.file_size or 0,
            "file_name": (
                f"sticker_animated_{int(time.time())}.webm"
                if animated
                else f"sticker_{int(time.time())}.webp"
            ),
            "mime_type": (
                "video/webm"
                if animated
                else "image/webp"
            ),
            "sticker": True,
            "animated": animated,
        }

    return None


# ============================================================
# DOWNLOAD FROM TELEGRAM
# ============================================================

async def download_from_telegram(
    bot,
    file_id,
    file_name
):
    """
    ACTUAL Telegram download.

    This function is ONLY called after confirmation.
    """

    safe_name = Path(file_name).name or "file"

    destination = (
        TEMP_DIR
        / f"upload_{int(time.time() * 1000)}_{safe_name}"
    )

    try:

        print(
            f"[URL] Starting Telegram download: {safe_name}"
        )

        telegram_file = await bot.get_file(file_id)

        await telegram_file.download_to_drive(
            custom_path=str(destination)
        )

        print(
            f"[URL] Telegram download complete: {destination}"
        )

        return destination

    except Exception as error:

        print(
            f"[URL] Telegram download error: {error}"
        )

        try:
            if destination.exists():
                destination.unlink()
        except Exception:
            pass

        return None


# ============================================================
# GOFILE UPLOAD
# ============================================================

async def upload_to_gofile(file_path):

    try:

        timeout = aiohttp.ClientTimeout(
            total=None,
            connect=30,
            sock_connect=30,
            sock_read=None,
        )

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            form = aiohttp.FormData()

            with open(file_path, "rb") as file_handle:

                form.add_field(
                    "file",
                    file_handle,
                    filename=Path(file_path).name,
                    content_type="application/octet-stream",
                )

                async with session.post(
                    GOFILE_UPLOAD_URL,
                    data=form,
                ) as response:

                    response_text = await response.text()

            print(
                f"[GOFILE] HTTP Status: {response.status}"
            )

            if response.status != 200:
                print(
                    response_text[:1000]
                )
                return None

            try:
                result = json.loads(response_text)

            except json.JSONDecodeError:
                print(
                    "[GOFILE] Invalid JSON response"
                )
                return None

            if result.get("status") != "ok":

                print(
                    f"[GOFILE] Upload failed: {result}"
                )

                return None

            return result

    except Exception as error:

        print(
            f"[GOFILE] Upload error: {error}"
        )

        return None


# ============================================================
# MAIN COMMAND
# ============================================================

async def execute(
    update,
    context,
    args=None,
    extra=None
):

    args = args or []

    # Callback protection
    if update and update.callback_query:

        await button_callback(
            update,
            context
        )

        return

    if not update or not update.message:
        return

    reply_message = (
        update.message.reply_to_message
    )

    # /url
    if not args and not reply_message:

        await show_menu(update)

        return

    # Reply to file
    if reply_message:

        await handle_reply(
            update,
            context,
            reply_message
        )

        return

    # URL argument
    await handle_url(
        update,
        args
    )


# ============================================================
# MENU
# ============================================================

async def show_menu(update):

    text = """╭━━━༺ <b>📦 URL / GOFILE</b> ༻━━━╮
┃
┃ 🔧 <b>COMMANDS</b> :
┃
┃ 📤 <b>UPLOAD FILE</b> :
┃ Reply to a file with:
┃ <code>/url</code>
┃
┃ 📥 <b>DOWNLOAD FROM URL</b> :
┃ <code>/url &lt;url&gt;</code>
┃
┃ 📋 <b>SUPPORTED FILES</b> :
┃ 📸 Images
┃ 🎵 Audio
┃ 🎬 Video
┃ 📄 Documents
┃ 🎨 Stickers
┃
┃ 💡 <b>EXAMPLES</b> :
┃ Reply to a file with <code>/url</code>
┃ <code>/url https://example.com/file.mp4</code>
┃
╰━━━━━━━━━━━━━━━━━━╯
<blockquote>ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ</blockquote>"""

    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )


# ============================================================
# DETECT FILE
# ============================================================

async def handle_reply(
    update,
    context,
    reply_message
):

    # Metadata only.
    info = extract_file_info(
        reply_message
    )

    if not info:

        await update.message.reply_text(
            "❌ <b>Unsupported file type</b>\n\n"
            "Supported: Images, Audio, Video, "
            "Documents and Stickers.",
            parse_mode="HTML"
        )

        return

    file_size = info["file_size"]

    max_size = get_max_size(
        info["file_type"]
    )

    # Check known size BEFORE download.
    if (
        file_size
        and file_size > max_size
    ):

        await update.message.reply_text(
            f"❌ <b>File too large</b>\n\n"
            f"📁 <b>Type:</b> "
            f"{esc(file_type_label("
            f"info['file_type'], "
            f"info['sticker'], "
            f"info['animated']))}\n"
            f"📦 <b>Size:</b> "
            f"{esc(format_size(file_size))}\n"
            f"📊 <b>Maximum:</b> "
            f"{esc(format_size(max_size))}",
            parse_mode="HTML"
        )

        return

    # ========================================================
    # IMPORTANT:
    # We save metadata ONLY.
    # No Telegram download happens here.
    # ========================================================

    context.user_data[
        "pending_upload"
    ] = info

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📤 Confirm Upload",
                    callback_data=CONFIRM_CALLBACK
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data=CANCEL_CALLBACK
                )
            ]
        ]
    )

    text = (
        "📤 <b>File detected</b>\n\n"

        f"📁 <b>Type:</b> "
        f"{esc(file_type_label("
        f"info['file_type'], "
        f"info['sticker'], "
        f"info['animated']))}\n"

        f"📦 <b>Size:</b> "
        f"{esc(format_size(file_size))}\n"

        f"📄 <b>Name:</b> "
        f"<code>{esc(info['file_name'])}</code>\n\n"

        "⚡ <b>Ready to upload to Gofile?</b>\n"
        "The file will only be downloaded "
        "after you confirm."
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ============================================================
# URL ARGUMENT
# ============================================================

async def handle_url(
    update,
    args
):

    url = args[0].strip()

    if not url.startswith(
        ("http://", "https://")
    ):

        await update.message.reply_text(
            "❌ <b>Invalid URL</b>\n\n"
            "Please provide a URL beginning "
            "with <code>http://</code> or "
            "<code>https://</code>.",
            parse_mode="HTML"
        )

        return

    await update.message.reply_text(
        "📥 <b>URL download</b>\n\n"
        "Direct URL downloading is not "
        "enabled in this version yet.\n\n"
        "💡 Reply to a Telegram file with "
        "<code>/url</code> to upload it "
        "to Gofile.",
        parse_mode="HTML"
    )


# ============================================================
# BUTTON HANDLER
# ============================================================

async def button_callback(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    # Ignore menu buttons.
    if data not in {
        CONFIRM_CALLBACK,
        CANCEL_CALLBACK
    }:
        return

    # IMPORTANT:
    # Answer immediately so the button stops spinning.
    await query.answer()

    # ========================================================
    # CANCEL
    # ========================================================

    if data == CANCEL_CALLBACK:

        context.user_data.pop(
            "pending_upload",
            None
        )

        await query.edit_message_text(
            "❌ <b>Upload cancelled.</b>",
            parse_mode="HTML"
        )

        return

    # ========================================================
    # CONFIRM
    # ========================================================

    pending = context.user_data.get(
        "pending_upload"
    )

    if not pending:

        await query.edit_message_text(
            "⚠️ <b>Session expired.</b>\n\n"
            "Reply to the file with "
            "<code>/url</code> again.",
            parse_mode="HTML"
        )

        return

    # Remove buttons immediately.
    # This prevents double-click uploads.

    await query.edit_message_text(
        "⏳ <b>Preparing upload...</b>\n\n"
        f"📄 <code>"
        f"{esc(pending['file_name'])}"
        f"</code>\n"
        f"📦 {esc(format_size("
        f"pending['file_size']))}\n\n"
        "⬇️ Downloading from Telegram...",
        parse_mode="HTML"
    )

    file_path = None

    try:

        # ====================================================
        # THIS IS THE FIRST ACTUAL DOWNLOAD.
        # ====================================================

        file_path = await download_from_telegram(
            context.bot,
            pending["file_id"],
            pending["file_name"]
        )

        if not file_path:

            await query.edit_message_text(
                "❌ <b>Telegram download failed.</b>\n\n"
                "Please try again.",
                parse_mode="HTML"
            )

            return

        # ====================================================
        # UPLOAD TO GOFILE
        # ====================================================

        await query.edit_message_text(
            "🚀 <b>Uploading to Gofile...</b>\n\n"
            f"📄 <code>"
            f"{esc(pending['file_name'])}"
            f"</code>\n"
            f"📦 {esc(format_size("
            f"pending['file_size']))}\n\n"
            "⚡ Please wait...",
            parse_mode="HTML"
        )

        result = await upload_to_gofile(
            file_path
        )

        if (
            result
            and result.get("status") == "ok"
        ):

            data = result.get(
                "data"
            ) or {}

            download_page = data.get(
                "downloadPage"
            )

            file_name = (
                data.get("fileName")
                or pending["file_name"]
            )

            if download_page:

                link_html = (
                    f'<a href="{esc(download_page)}">'
                    f'Open Gofile Link'
                    f'</a>'
                )

            else:
                link_html = "Link unavailable"

            await query.edit_message_text(
                "✅ <b>Upload Successful!</b>\n\n"

                f"📄 <b>File:</b> "
                f"<code>{esc(file_name)}</code>\n"

                f"📦 <b>Size:</b> "
                f"{esc(format_size("
                f"pending['file_size']))}\n\n"

                f"🔗 {link_html}\n\n"

                "<blockquote>"
                "ᴘᴏᴡᴇʀᴇᴅ ʙʏ "
                "ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ"
                "</blockquote>",

                parse_mode="HTML",
                disable_web_page_preview=True
            )

        else:

            error_message = (
                result.get(
                    "message",
                    "Unknown Gofile error"
                )
                if result
                else
                "No response from Gofile"
            )

            await query.edit_message_text(
                "❌ <b>Upload Failed</b>\n\n"
                f"Error: <code>"
                f"{esc(error_message)}"
                f"</code>\n\n"
                "Please try again later.",
                parse_mode="HTML"
            )

    except Exception as error:

        print(
            f"[URL] Upload error: {error}"
        )

        await query.edit_message_text(
            "❌ <b>Upload Failed</b>\n\n"
            f"Error: <code>"
            f"{esc(str(error)[:200])}"
            f"</code>",
            parse_mode="HTML"
        )

    finally:

        # Always delete temporary file.
        if file_path:

            try:

                path = Path(file_path)

                if path.exists():
                    path.unlink()

            except Exception as cleanup_error:

                print(
                    f"[URL] Cleanup error: "
                    f"{cleanup_error}"
                )

        context.user_data.pop(
            "pending_upload",
            None
        )


# ============================================================
# DO NOT REGISTER A CATCH-ALL CALLBACK HERE
# ============================================================

def register_handlers(application):
    """
    Callback routing is handled centrally in main.py.

    Do NOT add:
        CallbackQueryHandler(button_callback)

    here without a pattern, because that can steal menu callbacks.
    """
    return
    