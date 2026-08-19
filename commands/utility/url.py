"""
DEV ZIKKY TELEGRAM - URL / GOFILE

HYBRID ARCHITECTURE

<= 20 MB
    Telegram file
        ↓
    Telegram download
        ↓
    Gofile
        ↓
    Gofile URL

> 20 MB
    Telegram file
        ↓
    NO DOWNLOAD
        ↓
    SHA-256 reference/hash
        ↓
    SQLite metadata storage
        ↓
    /start=<hash>
        ↓
    Telegram sends original file using file_id

IMPORTANT:
The hash is NOT the file.
The hash is only the lookup key.

The actual large file remains stored by Telegram
and is referenced using file_id.
"""

import hashlib
import html
import json
import sqlite3
import time
from pathlib import Path

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ============================================================
# COMMAND CONFIG
# ============================================================

COMMAND_NAME = "url"

ALIASES = [
    "gofile",
    "upload",
    "download",
]

DESCRIPTION = (
    "Upload Telegram files to Gofile "
    "or create Telegram stored-file links"
)

ADMIN_ONLY = False
OWNER_ONLY = False
GROUP_ONLY = False
BOT_ADMIN_NEEDED = False


# ============================================================
# SIZE LIMITS
# ============================================================

# Telegram Bot API normal download limit.
# We deliberately use 20 MiB here.

TELEGRAM_DOWNLOAD_LIMIT = 20 * 1024 * 1024


MAX_IMAGE_SIZE = 20 * 1024 * 1024
MAX_AUDIO_SIZE = 80 * 1024 * 1024
MAX_VIDEO_SIZE = 500 * 1024 * 1024
MAX_DOCUMENT_SIZE = 1000 * 1024 * 1024


# ============================================================
# GOFILE
# ============================================================

GOFILE_UPLOAD_URL = (
    "https://upload.gofile.io/uploadfile"
)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

TEMP_DIR = BASE_DIR / "tmp"

TEMP_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# DATABASE
# ============================================================

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


DATABASE_PATH = DATA_DIR / "url_files.db"


# ============================================================
# CALLBACK DATA
# ============================================================

CONFIRM_CALLBACK = (
    "url_confirm_upload"
)

CANCEL_CALLBACK = (
    "url_cancel_upload"
)


# ============================================================
# HTML
# ============================================================

def esc(value):
    """
    Safely escape dynamic Telegram HTML.
    """

    return html.escape(
        str(value or "")
    )


# ============================================================
# FILE SIZE
# ============================================================

def format_size(size_bytes):
    """
    Convert bytes to readable size.
    """

    if not size_bytes:
        return "Unknown"

    try:
        size_bytes = int(
            size_bytes
        )
    except (
        TypeError,
        ValueError,
    ):
        return "Unknown"

    if size_bytes < 1024:
        return (
            f"{size_bytes} B"
        )

    if size_bytes < 1024 * 1024:
        return (
            f"{size_bytes / 1024:.1f} KB"
        )

    if size_bytes < 1024 * 1024 * 1024:
        return (
            f"{size_bytes / (1024 * 1024):.1f} MB"
        )

    return (
        f"{size_bytes / "
        f"(1024 * 1024 * 1024):.1f} GB"
    )


# ============================================================
# FILE TYPE
# ============================================================

def get_file_type(
    mime_type,
    file_name,
):
    """
    Determine general file type.
    """

    mime_type = (
        mime_type or ""
    ).lower()

    file_name = (
        file_name or ""
    ).lower()

    if mime_type.startswith(
        "image/"
    ):
        return "image"

    if mime_type.startswith(
        "audio/"
    ):
        return "audio"

    if mime_type.startswith(
        "video/"
    ):
        return "video"

    extension = Path(
        file_name
    ).suffix.lower()

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


def get_max_size(
    file_type,
):
    """
    Return application-level maximum size.
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
# STICKER
# ============================================================

def is_animated_sticker(
    sticker,
):
    """
    Detect animated/video stickers.
    """

    return bool(
        getattr(
            sticker,
            "is_animated",
            False,
        )
        or getattr(
            sticker,
            "is_video",
            False,
        )
        or getattr(
            sticker,
            "mime_type",
            "",
        )
        in {
            "video/webm",
            "video/mp4",
        }
    )


# ============================================================
# FILE EXTRACTION
# ============================================================

def extract_file_info(
    message,
):
    """
    Extract Telegram file metadata.

    NEVER downloads the file.
    """

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    if message.document:

        item = message.document

        file_name = (
            item.file_name
            or "document"
        )

        return {
            "file_id": item.file_id,
            "file_type": get_file_type(
                item.mime_type,
                file_name,
            ),
            "file_size": (
                item.file_size or 0
            ),
            "file_name": file_name,
            "mime_type": (
                item.mime_type or ""
            ),
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
            "file_size": (
                item.file_size or 0
            ),
            "file_name": (
                f"image_"
                f"{int(time.time())}.jpg"
            ),
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
            "file_size": (
                item.file_size or 0
            ),
            "file_name": (
                item.file_name
                or
                f"video_"
                f"{int(time.time())}.mp4"
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
            "file_size": (
                item.file_size or 0
            ),
            "file_name": (
                item.file_name
                or
                f"audio_"
                f"{int(time.time())}.mp3"
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
            "file_size": (
                item.file_size or 0
            ),
            "file_name": (
                f"voice_"
                f"{int(time.time())}.ogg"
            ),
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
            "file_size": (
                item.file_size or 0
            ),
            "file_name": (
                f"video_note_"
                f"{int(time.time())}.mp4"
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

        animated = (
            is_animated_sticker(
                item
            )
        )

        if animated:

            file_name = (
                f"sticker_animated_"
                f"{int(time.time())}.webm"
            )

            mime_type = (
                "video/webm"
            )

            file_type = "video"

        else:

            file_name = (
                f"sticker_"
                f"{int(time.time())}.webp"
            )

            mime_type = (
                "image/webp"
            )

            file_type = "image"

        return {
            "file_id": item.file_id,
            "file_type": file_type,
            "file_size": (
                item.file_size or 0
            ),
            "file_name": file_name,
            "mime_type": mime_type,
            "sticker": True,
            "animated": animated,
        }

    return None


# ============================================================
# HASH
# ============================================================

def generate_file_hash(
    file_id,
    file_name,
    file_size,
    user_id,
):
    """
    Generate deterministic-looking unique storage key.

    IMPORTANT:
    This is a reference ID, NOT a hash of the file bytes.

    We intentionally do not download the >20 MB file
    just to calculate a SHA-256 byte hash.

    Telegram's file_id is the actual file reference.
    """

    raw = (
        f"{file_id}|"
        f"{file_name}|"
        f"{file_size}|"
        f"{user_id}|"
        f"{time.time_ns()}"
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:32]


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_database():
    """
    Create the large-file table.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS
            stored_files (
                hash TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_name TEXT,
                mime_type TEXT,
                file_size INTEGER,
                sticker INTEGER DEFAULT 0,
                animated INTEGER DEFAULT 0,
                owner_id TEXT,
                created_at INTEGER
            )
            """
        )

        connection.commit()

    finally:

        connection.close()


init_database()


# ============================================================
# DATABASE SAVE
# ============================================================

def store_large_file(
    file_hash,
    info,
    user_id,
):
    """
    Store Telegram file reference.

    NO file bytes are stored locally.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:

        connection.execute(
            """
            INSERT OR REPLACE INTO
            stored_files (
                hash,
                file_id,
                file_type,
                file_name,
                mime_type,
                file_size,
                sticker,
                animated,
                owner_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_hash,
                info["file_id"],
                info["file_type"],
                info["file_name"],
                info["mime_type"],
                int(
                    info["file_size"] or 0
                ),
                int(
                    bool(
                        info["sticker"]
                    )
                ),
                int(
                    bool(
                        info["animated"]
                    )
                ),
                str(user_id),
                int(time.time()),
            ),
        )

        connection.commit()

    finally:

        connection.close()


# ============================================================
# DATABASE GET
# ============================================================

def get_stored_file(
    file_hash,
):
    """
    Retrieve large-file metadata.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:

        cursor = connection.execute(
            """
            SELECT
                hash,
                file_id,
                file_type,
                file_name,
                mime_type,
                file_size,
                sticker,
                animated,
                owner_id,
                created_at
            FROM stored_files
            WHERE hash = ?
            """,
            (
                file_hash,
            ),
        )

        row = cursor.fetchone()

    finally:

        connection.close()

    if not row:
        return None

    return {
        "hash": row[0],
        "file_id": row[1],
        "file_type": row[2],
        "file_name": row[3],
        "mime_type": row[4],
        "file_size": row[5],
        "sticker": bool(row[6]),
        "animated": bool(row[7]),
        "owner_id": row[8],
        "created_at": row[9],
    }


# ============================================================
# DATABASE DELETE
# ============================================================

def delete_stored_file(
    file_hash,
):
    """
    Delete metadata only.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:

        connection.execute(
            """
            DELETE FROM stored_files
            WHERE hash = ?
            """,
            (
                file_hash,
            ),
        )

        connection.commit()

    finally:

        connection.close()


# ============================================================
# TELEGRAM DOWNLOAD
# ============================================================

async def download_from_telegram(
    bot,
    file_id,
    file_name,
):
    """
    Download Telegram file.

    ONLY used for files <= 20 MB.
    """

    safe_name = (
        Path(file_name).name
        or "file"
    )

    destination = (
        TEMP_DIR
        /
        (
            f"upload_"
            f"{int(time.time() * 1000)}_"
            f"{safe_name}"
        )
    )

    try:

        print(
            "[URL] Telegram download: "
            f"{safe_name}"
        )

        telegram_file = (
            await bot.get_file(
                file_id
            )
        )

        await telegram_file.download_to_drive(
            custom_path=str(
                destination
            )
        )

        if not destination.exists():

            print(
                "[URL] Telegram reported "
                "success but file is missing."
            )

            return None

        return destination

    except Exception as error:

        print(
            "[URL] Telegram download error: "
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

async def upload_to_gofile(
    file_path,
):
    """
    Upload local file to Gofile.
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
                "[GOFILE] HTTP status: "
                f"{response.status}"
            )

            if response.status != 200:

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
                    "[GOFILE] Invalid JSON."
                )

                return None

            return result

    except Exception as error:

        print(
            "[GOFILE] Upload error: "
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

    if (
        update
        and update.callback_query
    ):

        await button_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    if (
        not update
        or not update.message
    ):
        return

    reply_message = (
        update.message.reply_to_message
    )

    # --------------------------------------------------------
    # /url
    # --------------------------------------------------------

    if (
        not args
        and not reply_message
    ):

        await show_menu(
            update
        )

        return

    # --------------------------------------------------------
    # REPLY FILE
    # --------------------------------------------------------

    if reply_message:

        await handle_reply(
            update,
            context,
            reply_message,
        )

        return

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    await handle_url(
        update,
        args,
    )


# ============================================================
# MENU
# ============================================================

async def show_menu(
    update,
):
    """
    URL command help.
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
        "┃ 📋 <b>SUPPORTED</b> :\n"
        "┃ 📸 Images\n"
        "┃ 🎵 Audio\n"
        "┃ 🎬 Video\n"
        "┃ 📄 Documents\n"
        "┃ 🎨 Stickers\n"
        "┃\n"
        "┃ ⚡ Files over 20 MB use\n"
        "┃ Telegram stored-file mode.\n"
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
# HANDLE REPLY
# ============================================================

async def handle_reply(
    update,
    context,
    reply_message,
):
    """
    Detect a replied file.

    DOES NOT download anything.
    """

    info = extract_file_info(
        reply_message
    )

    if not info:

        await update.message.reply_text(
            "❌ <b>Unsupported file type</b>",
            parse_mode="HTML",
        )

        return

    file_size = int(
        info["file_size"] or 0
    )

    max_size = get_max_size(
        info["file_type"]
    )

    # --------------------------------------------------------
    # APPLICATION MAXIMUM
    # --------------------------------------------------------

    if (
        file_size
        and file_size > max_size
    ):

        await update.message.reply_text(
            "❌ <b>File too large</b>\n\n"
            f"📦 <b>Size:</b> "
            f"{esc(format_size(file_size))}\n"
            f"📊 <b>Maximum:</b> "
            f"{esc(format_size(max_size))}",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # MODE
    # --------------------------------------------------------

    large_file = (
        file_size
        > TELEGRAM_DOWNLOAD_LIMIT
    )

    if large_file:

        mode_text = (
            "🗄️ <b>Storage mode:</b> "
            "Telegram reference\n\n"
            "⚡ The file will NOT be downloaded "
            "to the bot server."
        )

    else:

        mode_text = (
            "🚀 <b>Storage mode:</b> "
            "Gofile\n\n"
            "⚠️ The file will be downloaded "
            "after confirmation."
        )

    # --------------------------------------------------------
    # STORE PENDING
    # --------------------------------------------------------

    context.user_data[
        "pending_upload"
    ] = {
        **info,
        "large_file": large_file,
        "reply_chat_id": (
            reply_message.chat_id
        ),
        "reply_message_id": (
            reply_message.message_id
        ),
    }

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📤 Confirm",
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
        f"{mode_text}\n\n"
        "⚡ <b>Continue?</b>"
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
    """

    if not args:

        await show_menu(
            update
        )

        return

    url = str(
        args[0]
    ).strip()

    if not url.startswith(
        (
            "http://",
            "https://",
        )
    ):

        await update.message.reply_text(
            "❌ <b>Invalid URL</b>",
            parse_mode="HTML",
        )

        return

    await update.message.reply_text(
        "📥 <b>URL download</b>\n\n"
        "Direct URL downloading is not "
        "enabled in this version.\n\n"
        "Reply to a Telegram file with "
        "<code>/url</code> instead.",
        parse_mode="HTML",
    )


# ============================================================
# CALLBACK
# ============================================================

async def button_callback(
    update,
    context,
):
    """
    Confirm / Cancel handler.
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if data not in {
        CONFIRM_CALLBACK,
        CANCEL_CALLBACK,
    }:
        return

    try:

        await query.answer()

    except Exception as error:

        print(
            "[URL] Callback answer error: "
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
                "[URL] Cancel error: "
                f"{error}"
            )

        return

    # ========================================================
    # GET PENDING
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
    # DOUBLE CLICK PROTECTION
    # --------------------------------------------------------

    if pending.get(
        "processing"
    ):

        return

    pending = {
        **pending,
        "processing": True,
    }

    context.user_data[
        "pending_upload"
    ] = pending

    # ========================================================
    # LARGE FILE MODE
    # ========================================================

    if pending.get(
        "large_file"
    ):

        await handle_large_file(
            query,
            context,
            pending,
        )

        return

    # ========================================================
    # NORMAL <=20MB MODE
    # ========================================================

    await handle_normal_file(
        query,
        context,
        pending,
    )


# ============================================================
# LARGE FILE HANDLER
# ============================================================

async def handle_large_file(
    query,
    context,
    pending,
):
    """
    Store >20 MB file by Telegram file_id.

    NO Telegram download happens.
    """

    file_name = pending.get(
        "file_name",
        "file",
    )

    file_size = pending.get(
        "file_size",
        0,
    )

    user = query.from_user

    # --------------------------------------------------------
    # GENERATE REFERENCE
    # --------------------------------------------------------

    file_hash = generate_file_hash(
        pending["file_id"],
        file_name,
        file_size,
        user.id,
    )

    # --------------------------------------------------------
    # STORE FILE REFERENCE
    # --------------------------------------------------------

    try:

        store_large_file(
            file_hash,
            pending,
            user.id,
        )

    except Exception as error:

        print(
            "[URL] Database error: "
            f"{error}"
        )

        try:

            await query.edit_message_text(
                "❌ <b>Storage failed.</b>\n\n"
                "The file was not stored.",
                parse_mode="HTML",
            )

        except Exception:
            pass

        context.user_data.pop(
            "pending_upload",
            None,
        )

        return

    # --------------------------------------------------------
    # BOT USERNAME
    # --------------------------------------------------------

    try:

        bot_info = (
            await context.bot.get_me()
        )

        bot_username = (
            bot_info.username
        )

    except Exception as error:

        print(
            "[URL] Could not get bot username: "
            f"{error}"
        )

        try:

            await query.edit_message_text(
                "❌ <b>Could not generate link.</b>",
                parse_mode="HTML",
            )

        except Exception:
            pass

        context.user_data.pop(
            "pending_upload",
            None,
        )

        return

    share_link = (
        f"https://t.me/"
        f"{bot_username}"
        f"?start={file_hash}"
    )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    text = (
        "╭━━━༺ "
        "<b>✅ FILE STORED</b> "
        "༻━━━╮\n"
        "┃\n"
        f"┃ 📄 <b>File:</b> "
        f"<code>{esc(file_name)}</code>\n"
        f"┃ 📦 <b>Size:</b> "
        f"{esc(format_size(file_size))}\n"
        "┃\n"
        "┃ 🗄️ <b>Storage:</b>\n"
        "┃ Telegram stored-file mode\n"
        "┃\n"
        f"┃ 🔑 <b>Hash:</b>\n"
        f"┃ <code>{esc(file_hash)}</code>\n"
        "┃\n"
        "┃ 🔗 <b>Share Link:</b>\n"
        f"┃ <code>{esc(share_link)}</code>\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n"
        "<blockquote>"
        "ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ"
        "</blockquote>"
    )

    try:

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    except Exception as error:

        print(
            "[URL] Large-file success message error: "
            f"{error}"
        )

    finally:

        context.user_data.pop(
            "pending_upload",
            None,
        )


# ============================================================
# NORMAL FILE HANDLER
# ============================================================

async def handle_normal_file(
    query,
    context,
    pending,
):
    """
    <=20 MB Telegram → local temp → Gofile.
    """

    file_name = pending.get(
        "file_name",
        "file",
    )

    file_size = pending.get(
        "file_size",
        0,
    )

    file_path = None

    try:

        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        await query.edit_message_text(
            "⏳ <b>Preparing upload...</b>\n\n"
            f"📄 <code>{esc(file_name)}</code>\n"
            f"📦 {esc(format_size(file_size))}\n\n"
            "⬇️ <b>Downloading from Telegram...</b>",
            parse_mode="HTML",
        )

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        file_path = (
            await download_from_telegram(
                context.bot,
                pending["file_id"],
                file_name,
            )
        )

        if not file_path:

            await query.edit_message_text(
                "❌ <b>Telegram download failed.</b>\n\n"
                "Please try again.",
                parse_mode="HTML",
            )

            return

        # ----------------------------------------------------
        # ACTUAL SIZE
        # ----------------------------------------------------

        actual_size = (
            file_path.stat().st_size
        )

        max_size = get_max_size(
            pending["file_type"]
        )

        if actual_size > max_size:

            await query.edit_message_text(
                "❌ <b>File too large</b>\n\n"
                f"📦 <b>Downloaded:</b> "
                f"{esc(format_size(actual_size))}\n"
                f"📊 <b>Maximum:</b> "
                f"{esc(format_size(max_size))}",
                parse_mode="HTML",
            )

            return

        # ----------------------------------------------------
        # GOFILE
        # ----------------------------------------------------

        await query.edit_message_text(
            "🚀 <b>Uploading to Gofile...</b>\n\n"
            f"📄 <code>{esc(file_name)}</code>\n"
            f"📦 "
            f"{esc(format_size(actual_size))}\n\n"
            "⚡ <b>Please wait...</b>",
            parse_mode="HTML",
        )

        result = (
            await upload_to_gofile(
                file_path
            )
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if (
            result
            and result.get("status")
            == "ok"
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

            if download_page:

                link_html = (
                    f'<a href="'
                    f'{esc(download_page)}'
                    f'">'
                    "🔗 Open Gofile Link"
                    "</a>"
                )

            else:

                link_html = (
                    "🔗 Link unavailable"
                )

            success_text = (
                "╭━━━༺ "
                "<b>✅ UPLOAD SUCCESSFUL</b> "
                "༻━━━╮\n"
                "┃\n"
                f"┃ 📄 <b>File:</b> "
                f"<code>"
                f"{esc(uploaded_file_name)}"
                f"</code>\n"
                f"┃ 📦 <b>Size:</b> "
                f"{esc(format_size(actual_size))}\n"
                "┃\n"
                f"┃ {link_html}\n"
                "┃\n"
                "╰━━━━━━━━━━━━━━━━━━╯\n"
                "<blockquote>"
                "ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ"
                "</blockquote>"
            )

            await query.edit_message_text(
                success_text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

            return

        # ----------------------------------------------------
        # GOFILE FAILURE
        # ----------------------------------------------------

        if result:

            error_message = (
                result.get("message")
                or result.get("error")
                or "Unknown Gofile error"
            )

        else:

            error_message = (
                "No response from Gofile"
            )

        await query.edit_message_text(
            "❌ <b>Upload Failed</b>\n\n"
            f"Error: <code>"
            f"{esc(error_message)}"
            f"</code>",
            parse_mode="HTML",
        )

    except Exception as error:

        print(
            "[URL] Normal upload error: "
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

        except Exception:
            pass

    finally:

        # ----------------------------------------------------
        # DELETE TEMP FILE
        # ----------------------------------------------------

        if file_path:

            try:

                path = Path(
                    file_path
                )

                if path.exists():

                    path.unlink()

                    print(
                        "[URL] Temporary file "
                        f"deleted: {path}"
                    )

            except Exception as error:

                print(
                    "[URL] Cleanup error: "
                    f"{error}"
                )

        # ----------------------------------------------------
        # CLEAR PENDING
        # ----------------------------------------------------

        context.user_data.pop(
            "pending_upload",
            None,
        )


# ============================================================
# HANDLER REGISTRATION
# ============================================================

def register_handlers(
    application,
):
    """
    Callback routing remains centralized.

    Main callback router should forward:

        url_confirm_upload
        url_cancel_upload

    to:

        button_callback(update, context)
    """

    return
    
    
    
    