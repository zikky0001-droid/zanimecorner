"""
DEV ZIKKY TELEGRAM - URL / GOFILE Command

Features:
- Reply to a Telegram file with /url
- Confirmation BEFORE downloading the Telegram file
- Async Telegram download
- Async Gofile upload
- HTML formatting throughout
- Reliable Confirm / Cancel buttons
- Temporary-file cleanup
- File-size validation before download
- Safe escaping of dynamic content
"""

import html
import json
import time
from pathlib import Path

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ============================================================
# COMMAND CONFIG
# ============================================================

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

TEMP_DIR = Path(__file__).resolve().parent.parent.parent / "tmp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CALLBACK DATA
# ============================================================

# Keep these unique so they do not conflict with menu buttons.
CONFIRM_CALLBACK = "url_confirm_upload"
CANCEL_CALLBACK = "url_cancel_upload"


# ============================================================
# HTML HELPERS
# ============================================================

def esc(value):
    """
    Safely escape dynamic values for Telegram HTML.
    """
    return html.escape(str(value or ""))


# ============================================================
# FILE SIZE
# ============================================================

def format_size(size_bytes):
    """
    Convert bytes into a readable file size.
    """

    if not size_bytes:
        return "Unknown"

    try:
        size_bytes = int(size_bytes)
    except (TypeError, ValueError):
        return "Unknown"

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
    """
    Determine the general file type.
    """

    mime_type = (mime_type or "").lower()
    file_name = (file_name or "").lower()

    # MIME detection
    if mime_type.startswith("image/"):
        return "image"

    if mime_type.startswith("audio/"):
        return "audio"

    if mime_type.startswith("video/"):
        return "video"

    # Extension detection
    extension = Path(file_name).suffix.lower()

    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".bmp",
        ".svg",
    }

    audio_extensions = {
        ".mp3",
        ".wav",
        ".ogg",
        ".aac",
        ".flac",
        ".m4a",
    }

    video_extensions = {
        ".mp4",
        ".mov",
        ".avi",
        ".webm",
        ".mkv",
        ".mpeg",
        ".mpg",
    }

    if extension in image_extensions:
        return "image"

    if extension in audio_extensions:
        return "audio"

    if extension in video_extensions:
        return "video"

    return "document"


def get_max_size(file_type):
    """
    Return maximum allowed size for the file type.
    """

    limits = {
        "image": MAX_IMAGE_SIZE,
        "audio": MAX_AUDIO_SIZE,
        "video": MAX_VIDEO_SIZE,
        "document": MAX_DOCUMENT_SIZE,
    }

    return limits.get(
        file_type,
        MAX_DOCUMENT_SIZE,
    )


def file_type_label(
    file_type,
    sticker=False,
    animated=False,
):
    """
    Human-readable file type.
    """

    if sticker:
        if animated:
            return "🎨 Animated Sticker"

        return "🎨 Static Sticker"

    labels = {
        "image": "🖼️ Image",
        "audio": "🎵 Audio",
        "video": "🎬 Video",
        "document": "📄 Document",
    }

    return labels.get(
        file_type,
        "📁 File",
    )


# ============================================================
# STICKER DETECTION
# ============================================================

def is_animated_sticker(sticker):
    """
    Detect animated/video stickers.
    """

    return bool(
        getattr(sticker, "is_animated", False)
        or getattr(sticker, "is_video", False)
        or getattr(sticker, "mime_type", "")
        in {
            "video/webm",
            "video/mp4",
        }
    )


# ============================================================
# FILE EXTRACTION
# ============================================================

def extract_file_info(message):
    """
    Extract Telegram file metadata.

    IMPORTANT:
    This function DOES NOT download the file.

    The actual Telegram download only happens
    after the user presses Confirm Upload.
    """

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    if message.document:
        item = message.document

        file_name = item.file_name or "document"

        return {
            "file_id": item.file_id,
            "file_type": get_file_type(
                item.mime_type,
                file_name,
            ),
            "file_size": item.file_size or 0,
            "file_name": file_name,
            "mime_type": item.mime_type or "",
            "sticker": False,
            "animated": False,
        }

    # --------------------------------------------------------
    # PHOTO
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

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
            "mime_type": (
                item.mime_type
                or "video/mp4"
            ),
            "sticker": False,
            "animated": False,
        }

    # --------------------------------------------------------
    # AUDIO
    # --------------------------------------------------------

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
            "mime_type": (
                item.mime_type
                or "audio/mpeg"
            ),
            "sticker": False,
            "animated": False,
        }

    # --------------------------------------------------------
    # VOICE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # VIDEO NOTE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # STICKER
    # --------------------------------------------------------

    if message.sticker:
        item = message.sticker

        animated = is_animated_sticker(item)

        if animated:
            file_name = (
                f"sticker_animated_"
                f"{int(time.time())}.webm"
            )
            mime_type = "video/webm"
            file_type = "video"
        else:
            file_name = (
                f"sticker_{int(time.time())}.webp"
            )
            mime_type = "image/webp"
            file_type = "image"

        return {
            "file_id": item.file_id,
            "file_type": file_type,
            "file_size": item.file_size or 0,
            "file_name": file_name,
            "mime_type": mime_type,
            "sticker": True,
            "animated": animated,
        }

    return None


# ============================================================
# TELEGRAM DOWNLOAD
# ============================================================

async def download_from_telegram(
    bot,
    file_id,
    file_name,
):
    """
    Download the Telegram file.

    This function is ONLY called after confirmation.
    """

    safe_name = Path(file_name).name or "file"

    destination = (
        TEMP_DIR
        / (
            f"upload_"
            f"{int(time.time() * 1000)}_"
            f"{safe_name}"
        )
    )

    try:

        print(
            f"[URL] Starting Telegram download: "
            f"{safe_name}"
        )

        telegram_file = await bot.get_file(
            file_id
        )

        await telegram_file.download_to_drive(
            custom_path=str(destination)
        )

        if not destination.exists():
            print(
                "[URL] Download reported success "
                "but file does not exist."
            )
            return None

        print(
            f"[URL] Telegram download complete: "
            f"{destination}"
        )

        return destination

    except Exception as error:

        print(
            f"[URL] Telegram download error: "
            f"{error}"
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
    """
    Upload a local file to Gofile.
    """

    timeout = aiohttp.ClientTimeout(
        total=None,
        connect=30,
        sock_connect=30,
        sock_read=None,
    )

    try:

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            form = aiohttp.FormData()

            with open(
                file_path,
                "rb",
            ) as file_handle:

                form.add_field(
                    "file",
                    file_handle,
                    filename=Path(
                        file_path
                    ).name,
                    content_type=(
                        "application/octet-stream"
                    ),
                )

                async with session.post(
                    GOFILE_UPLOAD_URL,
                    data=form,
                ) as response:

                    response_text = (
                        await response.text()
                    )

            print(
                f"[GOFILE] HTTP Status: "
                f"{response.status}"
            )

            if response.status != 200:

                print(
                    "[GOFILE] HTTP error:"
                )
                print(
                    response_text[:1000]
                )

                return None

            try:

                result = json.loads(
                    response_text
                )

            except json.JSONDecodeError:

                print(
                    "[GOFILE] Invalid JSON response."
                )

                return None

            if result.get("status") != "ok":

                print(
                    f"[GOFILE] Upload failed: "
                    f"{result}"
                )

                return result

            return result

    except Exception as error:

        print(
            f"[GOFILE] Upload error: "
            f"{error}"
        )

        return None


# ============================================================
# MAIN COMMAND
# ============================================================

async def execute(
    update,
    context,
    args=None,
    extra=None,
):
    """
    Main command entry point.
    """

    args = args or []

    # --------------------------------------------------------
    # CALLBACK
    # --------------------------------------------------------

    if update and update.callback_query:

        await button_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    if not update or not update.message:
        return

    reply_message = (
        update.message.reply_to_message
    )

    # --------------------------------------------------------
    # /url
    # --------------------------------------------------------

    if not args and not reply_message:

        await show_menu(update)

        return

    # --------------------------------------------------------
    # REPLY TO FILE
    # --------------------------------------------------------

    if reply_message:

        await handle_reply(
            update,
            context,
            reply_message,
        )

        return

    # --------------------------------------------------------
    # /url <url>
    # --------------------------------------------------------

    await handle_url(
        update,
        args,
    )


# ============================================================
# MENU
# ============================================================

async def show_menu(update):
    """
    Show URL command help.
    """

    text = (
        "╭━━━༺ <b>📦 URL / GOFILE</b> ༻━━━╮\n"
        "┃\n"
        "┃ 🔧 <b>COMMANDS</b> :\n"
        "┃\n"
        "┃ 📤 <b>UPLOAD FILE</b> :\n"
        "┃ Reply to a file with:\n"
        "┃ <code>/url</code>\n"
        "┃\n"
        "┃ 📥 <b>DOWNLOAD FROM URL</b> :\n"
        "┃ <code>/url &lt;url&gt;</code>\n"
        "┃\n"
        "┃ 📋 <b>SUPPORTED FILES</b> :\n"
        "┃ 📸 Images\n"
        "┃ 🎵 Audio\n"
        "┃ 🎬 Video\n"
        "┃ 📄 Documents\n"
        "┃ 🎨 Stickers\n"
        "┃\n"
        "┃ 💡 <b>EXAMPLES</b> :\n"
        "┃ Reply to a file with "
        "<code>/url</code>\n"
        "┃ <code>/url "
        "https://example.com/file.mp4"
        "</code>\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n"
        "<blockquote>"
        "ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ"
        "</blockquote>"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
    )


# ============================================================
# HANDLE REPLIED FILE
# ============================================================

async def handle_reply(
    update,
    context,
    reply_message,
):
    """
    Detect the replied Telegram file.

    IMPORTANT:
    No download occurs here.
    """

    info = extract_file_info(
        reply_message
    )

    if not info:

        await update.message.reply_text(
            "❌ <b>Unsupported file type</b>\n\n"
            "Supported files:\n"
            "• Images\n"
            "• Audio\n"
            "• Video\n"
            "• Documents\n"
            "• Stickers",
            parse_mode="HTML",
        )

        return

    file_size = info["file_size"]

    max_size = get_max_size(
        info["file_type"]
    )

    # --------------------------------------------------------
    # SIZE CHECK
    # --------------------------------------------------------

    if (
        file_size
        and file_size > max_size
    ):

        type_label = file_type_label(
            info["file_type"],
            info["sticker"],
            info["animated"],
        )

        await update.message.reply_text(
            "❌ <b>File too large</b>\n\n"
            f"📁 <b>Type:</b> "
            f"{esc(type_label)}\n"
            f"📦 <b>Size:</b> "
            f"{esc(format_size(file_size))}\n"
            f"📊 <b>Maximum:</b> "
            f"{esc(format_size(max_size))}",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # STORE METADATA ONLY
    # --------------------------------------------------------

    context.user_data[
        "pending_upload"
    ] = info

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📤 Confirm Upload",
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

    type_label = file_type_label(
        info["file_type"],
        info["sticker"],
        info["animated"],
    )

    text = (
        "📤 <b>File detected</b>\n\n"
        f"📁 <b>Type:</b> "
        f"{esc(type_label)}\n"
        f"📦 <b>Size:</b> "
        f"{esc(format_size(file_size))}\n"
        f"📄 <b>Name:</b> "
        f"<code>{esc(info['file_name'])}</code>\n\n"
        "⚡ <b>Ready to upload to Gofile?</b>\n\n"
        "The file will only be downloaded "
        "from Telegram after you press "
        "<b>Confirm Upload</b>."
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ============================================================
# URL ARGUMENT
# ============================================================

async def handle_url(
    update,
    args,
):
    """
    Handle /url <url>.

    Direct URL downloading is intentionally
    kept separate from Telegram-file uploading.
    """

    if not args:

        await show_menu(update)

        return

    url = str(args[0]).strip()

    if not url.startswith(
        (
            "http://",
            "https://",
        )
    ):

        await update.message.reply_text(
            "❌ <b>Invalid URL</b>\n\n"
            "Please provide a URL beginning "
            "with <code>http://</code> or "
            "<code>https://</code>.",
            parse_mode="HTML",
        )

        return

    # Direct URL downloading is not implemented
    # in the current version.

    await update.message.reply_text(
        "📥 <b>URL download</b>\n\n"
        "Direct URL downloading is not "
        "enabled in this version yet.\n\n"
        "💡 To upload a Telegram file to "
        "Gofile, reply to the file with "
        "<code>/url</code>.",
        parse_mode="HTML",
    )


# ============================================================
# CALLBACK HANDLER
# ============================================================

async def button_callback(
    update,
    context,
):
    """
    Handle Confirm / Cancel buttons.
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    # --------------------------------------------------------
    # ONLY HANDLE OUR CALLBACKS
    # --------------------------------------------------------

    if data not in {
        CONFIRM_CALLBACK,
        CANCEL_CALLBACK,
    }:
        return

    # --------------------------------------------------------
    # ANSWER IMMEDIATELY
    #
    # This stops Telegram's button spinner.
    # --------------------------------------------------------

    try:
        await query.answer()
    except Exception as error:
        print(
            f"[URL] Callback answer error: "
            f"{error}"
        )

    # ========================================================
    # CANCEL
    # ========================================================

    if data == CANCEL_CALLBACK:

        context.user_data.pop(
            "pending_upload",
            None,
        )

        try:

            await query.edit_message_text(
                "❌ <b>Upload cancelled.</b>",
                parse_mode="HTML",
            )

        except Exception as error:

            print(
                f"[URL] Cancel edit error: "
                f"{error}"
            )

        return

    # ========================================================
    # CONFIRM
    # ========================================================

    pending = context.user_data.get(
        "pending_upload"
    )

    if not pending:

        try:

            await query.edit_message_text(
                "⚠️ <b>Session expired.</b>\n\n"
                "Reply to the file with "
                "<code>/url</code> again.",
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    # --------------------------------------------------------
    # PREVENT DOUBLE CLICK
    # --------------------------------------------------------

    context.user_data[
        "pending_upload"
    ] = {
        **pending,
        "processing": True,
    }

    file_name = pending.get(
        "file_name",
        "file",
    )

    file_size = pending.get(
        "file_size",
        0,
    )

    # --------------------------------------------------------
    # REMOVE BUTTONS / SHOW DOWNLOAD
    # --------------------------------------------------------

    try:

        await query.edit_message_text(
            "⏳ <b>Preparing upload...</b>\n\n"
            f"📄 <code>{esc(file_name)}</code>\n"
            f"📦 {esc(format_size(file_size))}\n\n"
            "⬇️ <b>Downloading from Telegram...</b>",
            parse_mode="HTML",
        )

    except Exception as error:

        print(
            f"[URL] Progress message error: "
            f"{error}"
        )

    file_path = None

    try:

        # ====================================================
        # ACTUAL TELEGRAM DOWNLOAD
        #
        # THIS IS THE FIRST DOWNLOAD.
        # ====================================================

        file_path = await download_from_telegram(
            context.bot,
            pending["file_id"],
            file_name,
        )

        if not file_path:

            try:

                await query.edit_message_text(
                    "❌ <b>Telegram download failed.</b>\n\n"
                    "Please try again.",
                    parse_mode="HTML",
                )

            except Exception:
                pass

            return

        # ----------------------------------------------------
        # CHECK ACTUAL DOWNLOADED SIZE
        # ----------------------------------------------------

        try:

            actual_size = (
                file_path.stat().st_size
            )

        except Exception:

            actual_size = 0

        max_size = get_max_size(
            pending["file_type"]
        )

        if (
            actual_size
            and actual_size > max_size
        ):

            try:

                await query.edit_message_text(
                    "❌ <b>File too large</b>\n\n"
                    f"📦 <b>Downloaded:</b> "
                    f"{esc(format_size(actual_size))}\n"
                    f"📊 <b>Maximum:</b> "
                    f"{esc(format_size(max_size))}",
                    parse_mode="HTML",
                )

            except Exception:
                pass

            return

        # ====================================================
        # GOFILE UPLOAD
        # ====================================================

        try:

            await query.edit_message_text(
                "🚀 <b>Uploading to Gofile...</b>\n\n"
                f"📄 <code>{esc(file_name)}</code>\n"
                f"📦 "
                f"{esc(format_size(actual_size or file_size))}\n\n"
                "⚡ <b>Please wait...</b>",
                parse_mode="HTML",
            )

        except Exception as error:

            print(
                f"[URL] Upload progress error: "
                f"{error}"
            )

        result = await upload_to_gofile(
            file_path
        )

        # ====================================================
        # SUCCESS
        # ====================================================

        if (
            result
            and result.get("status") == "ok"
        ):

            result_data = (
                result.get("data")
                or {}
            )

            download_page = (
                result_data.get(
                    "downloadPage"
                )
            )

            uploaded_file_name = (
                result_data.get(
                    "fileName"
                )
                or file_name
            )

            uploaded_size = (
                actual_size
                or file_size
            )

            if download_page:

                # Telegram HTML allows href attributes.
                # Escape the URL to avoid malformed markup.

                safe_download_page = esc(
                    download_page
                )

                link_html = (
                    f'<a href="{safe_download_page}">'
                    "🔗 Open Gofile Link"
                    "</a>"
                )

            else:

                link_html = (
                    "🔗 Link unavailable"
                )

            success_text = (
                "╭━━━༺ <b>✅ UPLOAD SUCCESSFUL</b> ༻━━━╮\n"
                "┃\n"
                f"┃ 📄 <b>File:</b> "
                f"<code>{esc(uploaded_file_name)}</code>\n"
                f"┃ 📦 <b>Size:</b> "
                f"{esc(format_size(uploaded_size))}\n"
                "┃\n"
                f"┃ {link_html}\n"
                "┃\n"
                "╰━━━━━━━━━━━━━━━━━━╯\n"
                "<blockquote>"
                "ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ"
                "</blockquote>"
            )

            try:

                await query.edit_message_text(
                    success_text,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )

            except Exception as error:

                print(
                    f"[URL] Success message error: "
                    f"{error}"
                )

            return

        # ====================================================
        # GOFILE FAILURE
        # ====================================================

        if result:

            error_message = result.get(
                "message"
            ) or result.get(
                "error"
            ) or "Unknown Gofile error"

        else:

            error_message = (
                "No response from Gofile"
            )

        try:

            await query.edit_message_text(
                "❌ <b>Upload Failed</b>\n\n"
                f"Error: <code>"
                f"{esc(error_message)}"
                f"</code>\n\n"
                "Please try again later.",
                parse_mode="HTML",
            )

        except Exception as error:

            print(
                f"[URL] Failure message error: "
                f"{error}"
            )

    except Exception as error:

        print(
            f"[URL] Upload error: "
            f"{error}"
        )

        try:

            await query.edit_message_text(
                "❌ <b>Upload Failed</b>\n\n"
                f"Error: <code>"
                f"{esc(str(error)[:300])}"
                f"</code>",
                parse_mode="HTML",
            )

        except Exception as edit_error:

            print(
                f"[URL] Error message edit failed: "
                f"{edit_error}"
            )

    finally:

        # ====================================================
        # CLEAN TEMP FILE
        # ====================================================

        if file_path:

            try:

                path = Path(file_path)

                if path.exists():
                    path.unlink()

                    print(
                        f"[URL] Temporary file "
                        f"deleted: {path}"
                    )

            except Exception as cleanup_error:

                print(
                    f"[URL] Cleanup error: "
                    f"{cleanup_error}"
                )

        # ====================================================
        # CLEAR PENDING UPLOAD
        # ====================================================

        context.user_data.pop(
            "pending_upload",
            None,
        )


# ============================================================
# HANDLER REGISTRATION
# ============================================================

def register_handlers(application):
    """
    Callback routing is handled centrally by main.py.

    Do NOT register a catch-all CallbackQueryHandler here.

    Your central callback router should forward:

        url_confirm_upload
        url_cancel_upload

    to:

        button_callback(update, context)

    without stealing unrelated menu callbacks.
    """

    return
    
    