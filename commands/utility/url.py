"""
URL Command - Download and upload files using Gofile API
Supports:
- Images
- Audio
- Video
- Documents
- Stickers (static + animated)

Uses HTML formatting instead of Markdown to prevent
Telegram "Can't parse entities" errors.
"""

import html
import json
import time
from pathlib import Path

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler


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


# ============================================================
# HTML HELPERS
# ============================================================

def escape_html(value):
    """
    Safely escape dynamic text before putting it inside
    Telegram HTML messages.
    """
    if value is None:
        return ""

    return html.escape(str(value), quote=False)


# ============================================================
# STICKER DETECTION
# ============================================================

def is_animated_sticker(sticker):
    """Check whether a Telegram sticker is animated/video."""

    if hasattr(sticker, "is_animated"):
        return bool(sticker.is_animated)

    if hasattr(sticker, "is_video"):
        return bool(sticker.is_video)

    mime_type = getattr(sticker, "mime_type", None)

    if mime_type:
        return mime_type in (
            "video/webm",
            "video/mp4",
        )

    return False


def is_static_sticker(sticker):
    """Check whether a Telegram sticker is static."""

    if is_animated_sticker(sticker):
        return False

    mime_type = getattr(sticker, "mime_type", None)

    if mime_type:
        return mime_type == "image/webp"

    return True


# ============================================================
# FILE TYPE HELPERS
# ============================================================

def get_file_type(mime_type, file_name, message):
    """Determine file type using MIME type or extension."""

    mime_type = mime_type or ""
    file_name = file_name or "file"

    # Sticker
    if message and getattr(message, "sticker", None):
        if is_animated_sticker(message.sticker):
            return "video"

        return "image"

    # Images
    image_types = (
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/bmp",
        "image/svg",
    )

    if mime_type.startswith(image_types):
        return "image"

    # Audio
    audio_types = (
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/ogg",
        "audio/aac",
        "audio/flac",
    )

    if mime_type.startswith(audio_types):
        return "audio"

    # Video
    video_types = (
        "video/mp4",
        "video/quicktime",
        "video/x-msvideo",
        "video/webm",
        "video/mpeg",
    )

    if mime_type.startswith(video_types):
        return "video"

    # Documents
    document_types = (
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument",
        "text/plain",
        "application/json",
        "application/zip",
        "application/x-rar-compressed",
    )

    if mime_type.startswith(document_types):
        return "document"

    # Extension fallback
    extension = (
        file_name.rsplit(".", 1)[-1].lower()
        if "." in file_name
        else ""
    )

    image_extensions = {
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp",
        "bmp",
        "svg",
    }

    audio_extensions = {
        "mp3",
        "wav",
        "ogg",
        "aac",
        "flac",
        "m4a",
    }

    video_extensions = {
        "mp4",
        "mov",
        "avi",
        "webm",
        "mkv",
        "mpeg",
    }

    if extension in image_extensions:
        return "image"

    if extension in audio_extensions:
        return "audio"

    if extension in video_extensions:
        return "video"

    return "document"


def get_max_size(file_type):
    """Return maximum allowed size."""

    sizes = {
        "image": MAX_IMAGE_SIZE,
        "audio": MAX_AUDIO_SIZE,
        "video": MAX_VIDEO_SIZE,
        "document": MAX_DOCUMENT_SIZE,
    }

    return sizes.get(file_type, MAX_DOCUMENT_SIZE)


def format_size(size_bytes):
    """Format bytes into readable size."""

    size_bytes = size_bytes or 0

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"

    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# ============================================================
# GOFILE UPLOAD
# ============================================================

async def upload_to_gofile(file_path, folder_id=None):
    """
    Upload a file to Gofile.

    Uses the current Gofile upload endpoint.
    """

    try:
        form = aiohttp.FormData()

        with open(file_path, "rb") as file_handle:

            form.add_field(
                "file",
                file_handle,
                filename=Path(file_path).name,
                content_type="application/octet-stream",
            )

            if folder_id:
                form.add_field(
                    "folderId",
                    str(folder_id),
                )

            timeout = aiohttp.ClientTimeout(
                total=None
            )

            async with aiohttp.ClientSession(
                timeout=timeout
            ) as session:

                async with session.post(
                    GOFILE_UPLOAD_URL,
                    data=form,
                ) as response:

                    response_text = await response.text()

                    print(
                        f"[GOFILE] HTTP Status: "
                        f"{response.status}"
                    )

                    print(
                        f"[GOFILE] Response: "
                        f"{response_text[:1000]}"
                    )

                    if response.status != 200:
                        return None

                    try:
                        result = json.loads(
                            response_text
                        )
                    except json.JSONDecodeError:
                        print(
                            "[GOFILE] Invalid JSON response"
                        )
                        return None

                    if result.get("status") == "ok":
                        return result

                    print(
                        f"[GOFILE] Upload failed: {result}"
                    )

                    return None

    except Exception as error:
        print(
            f"[GOFILE] Upload error: {error}"
        )

        return None


# ============================================================
# DOWNLOAD FILE FROM TELEGRAM
# ============================================================

async def download_file_from_telegram(
    bot,
    file_id,
    file_name=None,
):
    """Download a Telegram file to the temporary directory."""

    try:

        if not file_name:
            file_name = (
                f"file_{int(time.time())}"
            )

        safe_name = Path(file_name).name

        file_path = (
            TEMP_DIR
            / f"upload_{safe_name}_{int(time.time())}"
        )

        telegram_file = await bot.get_file(
            file_id
        )

        await telegram_file.download_to_drive(
            file_path
        )

        return file_path

    except Exception as error:

        print(
            f"[DOWNLOAD] Error: {error}"
        )

        return None


# ============================================================
# MAIN COMMAND
# ============================================================

async def execute(
    update,
    context,
    args,
    extra,
):
    """Main URL command."""

    # Callback button
    if update and update.callback_query:
        await button_callback(
            update,
            context,
        )
        return

    # Check for replied message
    reply_message = None

    if (
        update
        and update.message
        and update.message.reply_to_message
    ):
        reply_message = (
            update.message.reply_to_message
        )

    # No arguments and no reply
    if not args and not reply_message:

        await show_menu(
            update,
            context,
            extra,
        )

        return

    # Reply to a file
    if reply_message:

        await handle_reply(
            update,
            context,
            reply_message,
            extra,
        )

        return

    # URL argument
    await handle_url(
        update,
        context,
        args,
        extra,
    )


# ============================================================
# SHOW MENU
# ============================================================

async def show_menu(
    update,
    context,
    extra,
):
    """Display URL/Gofile help menu."""

    menu_text = """
╭━━━༺ <b>📦 URL / GOFILE</b> ༻━━━╮
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
┃ 📸 Images (20MB max)
┃ 🎵 Audio (80MB max)
┃ 🎬 Video (500MB max)
┃ 📄 Documents (1000MB max)
┃ 🎨 Stickers (Static &amp; Animated)
┃
┃ 💡 <b>EXAMPLES</b> :
┃ Reply to a file with <code>/url</code>
┃ <code>/url https://example.com/file.mp4</code>
┃
╰━━━━━━━━━━━━━━━━━━╯
&gt; <b>ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ</b>
"""

    if update and update.message:

        await update.message.reply_text(
            menu_text,
            parse_mode="HTML",
        )

        return

    reply = extra.get("reply")

    if reply:

        await reply(
            menu_text,
            parse_mode="HTML",
        )


# ============================================================
# HANDLE REPLY / FILE UPLOAD
# ============================================================

async def handle_reply(
    update,
    context,
    reply_message,
    extra,
):
    """Process a file that the user replied to."""

    file_info = None
    file_type = None
    file_size = 0
    file_name = "file"

    is_sticker = False
    is_animated = False

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    if reply_message.document:

        file_info = reply_message.document

        file_name = (
            file_info.file_name
            or "file"
        )

        file_type = get_file_type(
            file_info.mime_type,
            file_name,
            reply_message,
        )

        file_size = (
            file_info.file_size or 0
        )

    # --------------------------------------------------------
    # PHOTO
    # --------------------------------------------------------

    elif reply_message.photo:

        file_info = reply_message.photo[-1]

        file_type = "image"

        file_size = (
            file_info.file_size or 0
        )

        file_name = (
            f"image_{int(time.time())}.jpg"
        )

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    elif reply_message.video:

        file_info = reply_message.video

        file_type = "video"

        file_size = (
            file_info.file_size or 0
        )

        file_name = (
            file_info.file_name
            or f"video_{int(time.time())}.mp4"
        )

    # --------------------------------------------------------
    # AUDIO
    # --------------------------------------------------------

    elif reply_message.audio:

        file_info = reply_message.audio

        file_type = "audio"

        file_size = (
            file_info.file_size or 0
        )

        file_name = (
            file_info.file_name
            or f"audio_{int(time.time())}.mp3"
        )

    # --------------------------------------------------------
    # VOICE
    # --------------------------------------------------------

    elif reply_message.voice:

        file_info = reply_message.voice

        file_type = "audio"

        file_size = (
            file_info.file_size or 0
        )

        file_name = (
            f"voice_{int(time.time())}.ogg"
        )

    # --------------------------------------------------------
    # VIDEO NOTE
    # --------------------------------------------------------

    elif reply_message.video_note:

        file_info = reply_message.video_note

        file_type = "video"

        file_size = (
            file_info.file_size or 0
        )

        file_name = (
            f"video_note_{int(time.time())}.mp4"
        )

    # --------------------------------------------------------
    # STICKER
    # --------------------------------------------------------

    elif reply_message.sticker:

        file_info = reply_message.sticker

        is_sticker = True

        is_animated = is_animated_sticker(
            file_info
        )

        file_type = (
            "video"
            if is_animated
            else "image"
        )

        file_size = (
            file_info.file_size or 0
        )

        sticker_file_name = getattr(
            file_info,
            "file_name",
            None,
        )

        if sticker_file_name:

            file_name = sticker_file_name

        elif is_animated:

            file_name = (
                f"sticker_animated_"
                f"{int(time.time())}.webm"
            )

        else:

            file_name = (
                f"sticker_"
                f"{int(time.time())}.webp"
            )

    # --------------------------------------------------------
    # UNSUPPORTED
    # --------------------------------------------------------

    else:

        await update.message.reply_text(
            "❌ <b>Unsupported file type</b>\n\n"
            "Please reply to a valid file.\n\n"
            "Supported:\n"
            "📸 Images\n"
            "🎵 Audio\n"
            "🎬 Video\n"
            "📄 Documents\n"
            "🎨 Stickers",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # FILE DISPLAY
    # --------------------------------------------------------

    if is_sticker:

        file_type_display = (
            "🎨 Sticker (Animated)"
            if is_animated
            else "🎨 Sticker (Static)"
        )

        max_size = MAX_DOCUMENT_SIZE

    else:

        file_type_display = (
            file_type.capitalize()
        )

        max_size = get_max_size(
            file_type
        )

    # --------------------------------------------------------
    # SIZE CHECK
    # --------------------------------------------------------

    if file_size > max_size:

        await update.message.reply_text(
            f"❌ <b>File too large!</b>\n\n"
            f"📁 <b>Type:</b> "
            f"{escape_html(file_type_display)}\n"
            f"📦 <b>Size:</b> "
            f"{escape_html(format_size(file_size))}\n"
            f"📊 <b>Max allowed:</b> "
            f"{escape_html(format_size(max_size))}\n\n"
            "Please use a smaller file.",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # SAVE PENDING UPLOAD
    # --------------------------------------------------------

    context.user_data[
        "pending_upload"
    ] = {
        "file_id": file_info.file_id,
        "file_type": file_type,
        "file_size": file_size,
        "file_name": file_name,
        "mime_type": getattr(
            file_info,
            "mime_type",
            None,
        ),
        "is_sticker": is_sticker,
        "is_animated": is_animated,
        "file_type_display": file_type_display,
    }

    # --------------------------------------------------------
    # CONFIRMATION BUTTONS
    # --------------------------------------------------------

    keyboard = [
        [
            InlineKeyboardButton(
                "📤 Upload",
                callback_data="confirm_upload",
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="cancel_upload",
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    sticker_info = ""

    if is_sticker:

        sticker_info = (
            " 🎨 (Animated)"
            if is_animated
            else " 🎨"
        )

    await update.message.reply_text(
        f"📤 <b>File detected</b>"
        f"{escape_html(sticker_info)}\n\n"
        f"📁 <b>Type:</b> "
        f"{escape_html(file_type_display)}\n"
        f"📦 <b>Size:</b> "
        f"{escape_html(format_size(file_size))}\n"
        f"📄 <b>Name:</b> "
        f"{escape_html(file_name)}\n\n"
        "Would you like to upload this "
        "file to Gofile?",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )


# ============================================================
# HANDLE URL
# ============================================================

async def handle_url(
    update,
    context,
    args,
    extra,
):
    """Handle a URL argument."""

    if not args:

        await show_menu(
            update,
            context,
            extra,
        )

        return

    url = str(args[0]).strip()

    # --------------------------------------------------------
    # URL VALIDATION
    # --------------------------------------------------------

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):

        await update.message.reply_text(
            "❌ <b>Invalid URL</b>\n\n"
            "Please provide a valid URL starting "
            "with <code>http://</code> or "
            "<code>https://</code>.",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # GOFILE URL
    # --------------------------------------------------------

    if "gofile.io" in url.lower():

        await handle_gofile_url(
            update,
            context,
            url,
            extra,
        )

        return

    # --------------------------------------------------------
    # OTHER URL
    # --------------------------------------------------------

    await update.message.reply_text(
        f"📥 <b>Processing URL</b>\n\n"
        f"🔗 <code>{escape_html(url)}</code>\n\n"
        "⏳ <b>Fetching file information...</b>",
        parse_mode="HTML",
    )

    await update.message.reply_text(
        "⚠️ <b>URL download</b>\n\n"
        "Direct URL download is not implemented yet.\n\n"
        "💡 For now, download the file and "
        "send it here, or use a Gofile link.",
        parse_mode="HTML",
    )


# ============================================================
# HANDLE GOFILE URL
# ============================================================

async def handle_gofile_url(
    update,
    context,
    url,
    extra,
):
    """Handle a Gofile URL."""

    file_id = None

    # /d/FILE_ID
    if "/d/" in url:

        file_id = (
            url.split("/d/", 1)[1]
            .split("/", 1)[0]
            .split("?", 1)[0]
        )

    # ?fileId=FILE_ID
    elif "?fileId=" in url:

        file_id = (
            url.split("?fileId=", 1)[1]
            .split("&", 1)[0]
        )

    # --------------------------------------------------------
    # INVALID GOFILE URL
    # --------------------------------------------------------

    if not file_id:

        await update.message.reply_text(
            "❌ <b>Invalid Gofile URL</b>\n\n"
            "Could not extract the file ID.",
            parse_mode="HTML",
        )

        return

    safe_file_id = escape_html(
        file_id
    )

    await update.message.reply_text(
        f"📥 <b>Gofile URL detected</b>\n\n"
        f"🔗 <b>File ID:</b> "
        f"<code>{safe_file_id}</code>\n\n"
        "⏳ <b>Fetching file...</b>",
        parse_mode="HTML",
    )

    # --------------------------------------------------------
    # DOWNLOAD TODO
    # --------------------------------------------------------

    await update.message.reply_text(
        "⚠️ <b>Gofile download</b>\n\n"
        "Direct Gofile download is not "
        "implemented yet.\n\n"
        "💡 Please download the file manually "
        "and send it here for upload.",
        parse_mode="HTML",
    )


# ============================================================
# BUTTON CALLBACK HANDLER
# ============================================================

async def button_callback(
    update,
    context,
):
    """Handle Upload / Cancel buttons."""

    query = update.callback_query

    data = query.data

    await query.answer()

    # ========================================================
    # CANCEL
    # ========================================================

    if data == "cancel_upload":

        context.user_data.pop(
            "pending_upload",
            None,
        )

        await query.edit_message_text(
            "❌ <b>Upload cancelled.</b>",
            parse_mode="HTML",
        )

        return

    # ========================================================
    # CONFIRM UPLOAD
    # ========================================================

    if data != "confirm_upload":
        return

    pending = context.user_data.get(
        "pending_upload"
    )

    # --------------------------------------------------------
    # SESSION EXPIRED
    # --------------------------------------------------------

    if not pending:

        await query.edit_message_text(
            "❌ <b>Session expired.</b>\n\n"
            "Please send the file again.",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # UPLOADING MESSAGE
    # --------------------------------------------------------

    await query.edit_message_text(
        f"⏳ <b>Uploading file to Gofile...</b>\n\n"
        f"📁 <b>Type:</b> "
        f"{escape_html(pending.get('file_type_display', 'unknown'))}\n"
        f"📦 <b>Size:</b> "
        f"{escape_html(format_size(pending.get('file_size', 0)))}\n"
        f"📄 <b>Name:</b> "
        f"{escape_html(pending.get('file_name', 'file'))}\n\n"
        "Please wait...",
        parse_mode="HTML",
    )

    file_path = None

    try:

        # ----------------------------------------------------
        # DOWNLOAD FROM TELEGRAM
        # ----------------------------------------------------

        file_path = (
            await download_file_from_telegram(
                query.message.bot,
                pending["file_id"],
                pending.get(
                    "file_name",
                    "file",
                ),
            )
        )

        if not file_path:

            await query.edit_message_text(
                "❌ <b>Failed to download file.</b>\n\n"
                "Please try again.",
                parse_mode="HTML",
            )

            return

        # ----------------------------------------------------
        # UPLOAD TO GOFILE
        # ----------------------------------------------------

        result = await upload_to_gofile(
            file_path
        )

        # ----------------------------------------------------
        # CLEAN TEMP FILE
        # ----------------------------------------------------

        try:

            file_path.unlink()

        except Exception:

            pass

        file_path = None

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if (
            result
            and result.get("status") == "ok"
        ):

            result_data = result.get(
                "data",
                {},
            )

            download_page = (
                result_data.get(
                    "downloadPage"
                )
            )

            file_name = (
                result_data.get(
                    "fileName"
                )
                or pending.get(
                    "file_name",
                    "file",
                )
            )

            safe_file_name = escape_html(
                file_name
            )

            safe_download_page = escape_html(
                download_page
                or "Unavailable"
            )

            await query.edit_message_text(
                f"✅ <b>Upload Successful!</b>\n\n"
                f"📄 <b>File:</b> "
                f"{safe_file_name}\n"
                f"📦 <b>Size:</b> "
                f"{escape_html(format_size(pending.get('file_size', 0)))}\n\n"
                f"🔗 <b>Link:</b>\n"
                f"<code>{safe_download_page}</code>\n\n"
                "💡 The file is now available "
                "at the link above.",
                parse_mode="HTML",
            )

        # ----------------------------------------------------
        # FAILED
        # ----------------------------------------------------

        else:

            error_message = (
                result.get(
                    "message",
                    "Unknown error",
                )
                if result
                else "No response from Gofile"
            )

            await query.edit_message_text(
                "❌ <b>Upload Failed</b>\n\n"
                "Could not upload the file "
                "to Gofile.\n\n"
                f"⚠️ <b>Error:</b> "
                f"{escape_html(error_message)}\n\n"
                "Please try again later.",
                parse_mode="HTML",
            )

    # ========================================================
    # EXCEPTION
    # ========================================================

    except Exception as error:

        print(
            f"[UPLOAD] Error: {error}"
        )

        await query.edit_message_text(
            "❌ <b>Upload Failed</b>\n\n"
            f"⚠️ <b>Error:</b> "
            f"{escape_html(str(error)[:300])}\n\n"
            "Please try again later.",
            parse_mode="HTML",
        )

    finally:

        # ----------------------------------------------------
        # EXTRA CLEANUP
        # ----------------------------------------------------

        if file_path:

            try:
                file_path.unlink()

            except Exception:
                pass

        context.user_data.pop(
            "pending_upload",
            None,
        )


# ============================================================
# REGISTER CALLBACK HANDLER
# ============================================================

def register_handlers(application):
    """Register URL callback handlers."""

    application.add_handler(
        CallbackQueryHandler(
            button_callback,
            pattern="^(confirm_upload|cancel_upload)$",
        )
    )
    
    
    