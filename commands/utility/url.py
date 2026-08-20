"""
DEV ZIKKY TELEGRAM - URL / GOFILE Command

Features:
- /url
- /gofile
- /upload
- /download

Telegram file workflow:
    Telegram
       ↓
    /url
       ↓
    Confirmation
       ↓
    ZTGP2 / MTProto
       ↓
    Gofile
       ↓
    Download URL

IMPORTANT:
- The Python bot DOES NOT download the Telegram file.
- Telegram file metadata is read first.
- The actual file transfer is performed by ZTGP2 using MTProto.
- No 20 MB / 500 MB / 1 GB application ceiling is enforced here.
- ZTGP2 must have access to the Telegram message through MTProto.

Direct /url <http(s)://...> handling remains separate.
"""

# ============================================================
# IMPORTS
# ============================================================

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

COMMAND_NAME = "url"

ALIASES = [
    "gofile",
    "upload",
    "download",
]

DESCRIPTION = (
    "Download and upload files using ZTGP2 MTProto + Gofile"
)

ADMIN_ONLY = False
OWNER_ONLY = False
GROUP_ONLY = False
BOT_ADMIN_NEEDED = False


# ============================================================
# ZTGP2 CONFIGURATION
# ============================================================

ZTGP2_URL = "https://ztgp2.onrender.com"

TRANSFER_URL = (
    f"{ZTGP2_URL}/transfer"
)


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
# REQUEST CONFIGURATION
# ============================================================

# Large transfers can take a long time.
#
# total=None means aiohttp itself does not impose a total
# request timeout. ZTGP2 / Render / Gofile can still have
# their own infrastructure limits.

REQUEST_TIMEOUT = aiohttp.ClientTimeout(
    total=None,
    connect=60,
    sock_connect=60,
    sock_read=None,
)


# ============================================================
# REQUEST AGE
# ============================================================

# A confirmation request older than this is rejected.

PENDING_REQUEST_TIMEOUT = (
    15 * 60
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
    # MIME detection
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Extension detection
    # --------------------------------------------------------

    extension = ""

    try:
        from pathlib import Path

        extension = (
            Path(file_name)
            .suffix
            .lower()
        )
    except Exception:
        pass

    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".bmp",
        ".svg",
        ".tiff",
        ".tif",
        ".ico",
    }

    audio_extensions = {
        ".mp3",
        ".wav",
        ".ogg",
        ".aac",
        ".flac",
        ".m4a",
        ".opus",
        ".wma",
    }

    video_extensions = {
        ".mp4",
        ".mov",
        ".avi",
        ".webm",
        ".mkv",
        ".mpeg",
        ".mpg",
        ".flv",
        ".3gp",
        ".m4v",
        ".wmv",
    }

    if extension in image_extensions:
        return "image"

    if extension in audio_extensions:
        return "audio"

    if extension in video_extensions:
        return "video"

    return "document"


# ============================================================
# FILE TYPE LABEL
# ============================================================

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

    IMPORTANT:
    This function NEVER downloads the file.

    It only obtains metadata already available in
    the Telegram message object.
    """

    if not message:
        return None

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
                f"image_{int(time.time())}.jpg"
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

        file_name = (
            item.file_name
            or f"video_{int(time.time())}.mp4"
        )

        return {
            "file_id": item.file_id,
            "file_type": "video",
            "file_size": (
                item.file_size or 0
            ),
            "file_name": file_name,
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

        file_name = (
            item.file_name
            or f"audio_{int(time.time())}.mp3"
        )

        return {
            "file_id": item.file_id,
            "file_type": "audio",
            "file_size": (
                item.file_size or 0
            ),
            "file_name": file_name,
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
                f"voice_{int(time.time())}.ogg"
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
                f"video_note_{int(time.time())}.mp4"
            ),
            "mime_type": "video/mp4",
            "sticker": False,
            "animated": False,
        }

    # --------------------------------------------------------
    # ANIMATION
    # --------------------------------------------------------

    if message.animation:

        item = message.animation

        file_name = (
            item.file_name
            or f"animation_{int(time.time())}.mp4"
        )

        return {
            "file_id": item.file_id,
            "file_type": "video",
            "file_size": (
                item.file_size or 0
            ),
            "file_name": file_name,
            "mime_type": (
                item.mime_type
                or "video/mp4"
            ),
            "sticker": False,
            "animated": False,
        }

    # --------------------------------------------------------
    # STICKER
    # --------------------------------------------------------

    if message.sticker:

        item = message.sticker

        animated = is_animated_sticker(
            item
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
# ZTGP2 TRANSFER
# ============================================================

async def transfer_with_ztgp2(
    chat_id,
    message_id,
    file_name,
):
    """
    Ask ZTGP2 to retrieve the Telegram message through
    MTProto and upload it to Gofile.

    IMPORTANT:

    The Python bot does NOT download the Telegram file.

    ZTGP2 receives:
        chat_id
        message_id
        file_name

    and performs the actual Telegram -> Gofile transfer.
    """

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "file_name": file_name,
    }

    print(
        "[URL] Starting ZTGP2 transfer"
    )

    print(
        "[URL] Transfer URL: "
        f"{TRANSFER_URL}"
    )

    print(
        "[URL] chat_id="
        f"{chat_id}, message_id="
        f"{message_id}"
    )

    try:

        async with aiohttp.ClientSession(
            timeout=REQUEST_TIMEOUT
        ) as session:

            async with session.post(
                TRANSFER_URL,
                json=payload,
            ) as response:

                status = (
                    response.status
                )

                response_text = (
                    await response.text()
                )

        print(
            "[URL] ZTGP2 HTTP status: "
            f"{status}"
        )

        print(
            "[URL] ZTGP2 response: "
            f"{response_text[:2000]}"
        )

        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        try:

            result = json.loads(
                response_text
            )

        except json.JSONDecodeError:

            return {
                "success": False,
                "error": (
                    "ZTGP2 returned invalid JSON."
                ),
                "http_status": status,
            }

        # ----------------------------------------------------
        # HTTP ERROR
        # ----------------------------------------------------

        if status < 200 or status >= 300:

            error = (
                result.get("error")
                or result.get("message")
                or f"ZTGP2 HTTP {status}"
            )

            return {
                "success": False,
                "error": str(error),
                "http_status": status,
            }

        # ----------------------------------------------------
        # SUCCESS / FAILURE
        # ----------------------------------------------------

        if not result.get(
            "success",
            False,
        ):

            error = (
                result.get("error")
                or result.get("message")
                or "ZTGP2 transfer failed."
            )

            return {
                **result,
                "success": False,
                "error": str(error),
                "http_status": status,
            }

        return {
            **result,
            "success": True,
            "http_status": status,
        }

    except aiohttp.ClientError as error:

        print(
            "[URL] ZTGP2 connection error: "
            f"{error}"
        )

        return {
            "success": False,
            "error": (
                f"Could not connect to ZTGP2: "
                f"{error}"
            ),
        }

    except asyncio.TimeoutError:

        print(
            "[URL] ZTGP2 transfer timeout"
        )

        return {
            "success": False,
            "error": (
                "ZTGP2 transfer timed out."
            ),
        }

    except Exception as error:

        print(
            "[URL] ZTGP2 unexpected error: "
            f"{error}"
        )

        return {
            "success": False,
            "error": str(error),
        }


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

    Supports:

        /url
        /gofile
        /upload
        /download

    Reply to a file with the command.

    Also preserves:

        /url <http(s)://...>
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
    # /url WITHOUT REPLY
    # --------------------------------------------------------

    if not args and not reply_message:

        await show_menu(
            update
        )

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

async def show_menu(
    update,
):
    """
    Show URL command help.
    """

    text = (
        "╭━━━༺ "
        "<b>📦 URL / GOFILE</b> "
        "༻━━━╮\n"
        "┃\n"
        "┃ 🔧 <b>COMMANDS</b> :\n"
        "┃\n"
        "┃ 📤 <b>UPLOAD FILE</b> :\n"
        "┃ Reply to a Telegram file with:\n"
        "┃ <code>/url</code>\n"
        "┃\n"
        "┃ 📥 <b>DOWNLOAD FROM URL</b> :\n"
        "┃ <code>/url &lt;url&gt;</code>\n"
        "┃\n"
        "┃ 📋 <b>SUPPORTED FILES</b> :\n"
        "┃ 🖼️ Images\n"
        "┃ 🎵 Audio\n"
        "┃ 🎬 Video\n"
        "┃ 📄 Documents\n"
        "┃ 🎨 Stickers\n"
        "┃ 🎙️ Voice\n"
        "┃\n"
        "┃ ⚡ <b>TRANSFER</b> :\n"
        "┃ MTProto → Gofile\n"
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

    No file download happens here.

    Only metadata is collected and stored.
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
            "• Stickers\n"
            "• Voice messages\n"
            "• Video notes",
            parse_mode="HTML",
        )

        return

    file_size = (
        info.get(
            "file_size",
            0,
        )
    )

    type_label = file_type_label(
        info.get(
            "file_type"
        ),
        info.get(
            "sticker",
            False,
        ),
        info.get(
            "animated",
            False,
        ),
    )

    # --------------------------------------------------------
    # NO APPLICATION SIZE LIMIT
    # --------------------------------------------------------
    #
    # IMPORTANT:
    #
    # There is deliberately NO:
    #
    #     if file_size > 20MB
    #
    #     if file_size > 500MB
    #
    #     if file_size > 1GB
    #
    # check here.
    #
    # ZTGP2/MTProto handles the actual transfer.
    # --------------------------------------------------------

    # --------------------------------------------------------
    # STORE COMPLETE REQUEST
    # --------------------------------------------------------

    context.user_data[
        "pending_upload"
    ] = {
        "chat_id": reply_message.chat_id,

        "message_id": (
            reply_message.message_id
        ),

        "file_id": info.get(
            "file_id"
        ),

        "file_type": info.get(
            "file_type"
        ),

        "file_size": file_size,

        "file_name": info.get(
            "file_name",
            "file",
        ),

        "mime_type": info.get(
            "mime_type",
            "",
        ),

        "sticker": info.get(
            "sticker",
            False,
        ),

        "animated": info.get(
            "animated",
            False,
        ),

        "created": time.time(),

        "processing": False,
    }

    # --------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CONFIRMATION
    # --------------------------------------------------------

    text = (
        "╭━━━༺ "
        "<b>📤 FILE DETECTED</b> "
        "༻━━━╮\n"
        "┃\n"
        f"┃ 📁 <b>Type:</b> "
        f"{esc(type_label)}\n"
        f"┃ 📦 <b>Size:</b> "
        f"{esc(format_size(file_size))}\n"
        f"┃ 📄 <b>Name:</b> "
        f"<code>{esc(info['file_name'])}</code>\n"
        "┃\n"
        "┃ ⚡ <b>Transfer:</b>\n"
        "┃ Telegram → MTProto → Gofile\n"
        "┃\n"
        "┃ 🚀 <b>No Bot API file download</b>\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        "⚠️ <b>Ready to transfer this file?</b>\n\n"
        "The file will be retrieved by "
        "<b>ZTGP2 using MTProto</b> only "
        "after you press "
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
    Handle:

        /url <url>

    Direct URL downloading remains separate from
    Telegram-file uploading.

    This version does not perform direct URL
    downloading yet.
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
            "❌ <b>Invalid URL</b>\n\n"
            "Please provide a URL beginning "
            "with <code>http://</code> or "
            "<code>https://</code>.",
            parse_mode="HTML",
        )

        return

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
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Handle Confirm / Cancel buttons.

    This function is called by the central callback
    router in main.py.
    """

    query = (
        update.callback_query
    )

    if not query:
        return

    data = (
        query.data or ""
    )

    # --------------------------------------------------------
    # ONLY HANDLE OUR CALLBACKS
    # --------------------------------------------------------

    if data not in {
        CONFIRM_CALLBACK,
        CANCEL_CALLBACK,
    }:
        return

    # --------------------------------------------------------
    # ANSWER CALLBACK
    # --------------------------------------------------------

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
                "[URL] Cancel edit error: "
                f"{error}"
            )

        return

    # ========================================================
    # CONFIRM
    # ========================================================

    pending = (
        context.user_data.get(
            "pending_upload"
        )
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
    # REQUEST AGE
    # --------------------------------------------------------

    created = pending.get(
        "created",
        0,
    )

    if (
        time.time() - created
        > PENDING_REQUEST_TIMEOUT
    ):

        context.user_data.pop(
            "pending_upload",
            None,
        )

        try:

            await query.edit_message_text(
                "⌛ <b>Upload request expired.</b>\n\n"
                "Reply to the file again with "
                "<code>/url</code>.",
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    # --------------------------------------------------------
    # DOUBLE CLICK PROTECTION
    # --------------------------------------------------------

    if pending.get(
        "processing",
        False,
    ):

        try:

            await query.answer(
                "⏳ Upload is already processing..."
            )

        except Exception:
            pass

        return

    # --------------------------------------------------------
    # MARK PROCESSING
    # --------------------------------------------------------

    pending[
        "processing"
    ] = True

    context.user_data[
        "pending_upload"
    ] = pending

    # --------------------------------------------------------
    # INFORMATION
    # --------------------------------------------------------

    file_name = (
        pending.get(
            "file_name",
            "file",
        )
    )

    file_size = (
        pending.get(
            "file_size",
            0,
        )
    )

    chat_id = (
        pending.get(
            "chat_id"
        )
    )

    message_id = (
        pending.get(
            "message_id"
        )
    )

    # --------------------------------------------------------
    # SHOW START STATUS
    # --------------------------------------------------------

    try:

        await query.edit_message_text(
            "⏳ <b>Preparing MTProto transfer...</b>\n\n"
            f"📄 <b>File:</b> "
            f"<code>{esc(file_name)}</code>\n"
            f"📦 <b>Size:</b> "
            f"{esc(format_size(file_size))}\n\n"
            "📡 <b>Connecting to ZTGP2...</b>\n"
            "⚡ <b>MTProto transfer will begin...</b>\n\n"
            "Please wait...",
            parse_mode="HTML",
        )

    except Exception as error:

        print(
            "[URL] Start progress error: "
            f"{error}"
        )

    # ========================================================
    # ZTGP2 TRANSFER
    # ========================================================

    try:

        result = await transfer_with_ztgp2(
            chat_id=chat_id,
            message_id=message_id,
            file_name=file_name,
        )

        # ====================================================
        # TRANSFER FAILURE
        # ====================================================

        if not result.get(
            "success",
            False,
        ):

            error_message = (
                result.get(
                    "error"
                )
                or result.get(
                    "message"
                )
                or "Unknown ZTGP2 transfer error."
            )

            context.user_data.pop(
                "pending_upload",
                None,
            )

            try:

                await query.edit_message_text(
                    "❌ <b>TRANSFER FAILED</b>\n\n"
                    f"📄 <b>File:</b> "
                    f"<code>{esc(file_name)}</code>\n"
                    f"📦 <b>Size:</b> "
                    f"{esc(format_size(file_size))}\n\n"
                    "📡 <b>ZTGP2:</b> Failed\n\n"
                    f"❗ <code>"
                    f"{esc(str(error_message)[:1500])}"
                    f"</code>\n\n"
                    "Please try again.",
                    parse_mode="HTML",
                )

            except Exception as error:

                print(
                    "[URL] Failure message error: "
                    f"{error}"
                )

            return

        # ====================================================
        # GET URL
        # ====================================================

        download_url = (
            result.get(
                "url"
            )
        )

        # Some ZTGP2 versions may return
        # downloadPage instead.
        if not download_url:

            download_url = (
                result.get(
                    "downloadPage"
                )
            )

        if not download_url:

            data = (
                result.get(
                    "data"
                )
                or {}
            )

            download_url = (
                data.get(
                    "downloadPage"
                )
                or data.get(
                    "url"
                )
            )

        # ----------------------------------------------------
        # NO URL
        # ----------------------------------------------------

        if not download_url:

            context.user_data.pop(
                "pending_upload",
                None,
            )

            try:

                await query.edit_message_text(
                    "⚠️ <b>Transfer completed</b>\n\n"
                    "ZTGP2 reported success, "
                    "but no Gofile URL was returned.",
                    parse_mode="HTML",
                )

            except Exception:
                pass

            return

        # ====================================================
        # RESULT DATA
        # ====================================================

        returned_name = (
            result.get(
                "file_name"
            )
            or result.get(
                "filename"
            )
            or file_name
        )

        returned_size = (
            result.get(
                "size_human"
            )
            or result.get(
                "size"
            )
            or format_size(
                file_size
            )
        )

        # ====================================================
        # SUCCESS BUTTON
        # ====================================================

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔗 Open Gofile Link",
                        url=str(
                            download_url
                        ),
                    )
                ]
            ]
        )

        # ====================================================
        # SUCCESS MESSAGE
        # ====================================================

        success_text = (
            "╭━━━༺ "
            "<b>✅ UPLOAD SUCCESSFUL</b> "
            "༻━━━╮\n"
            "┃\n"
            f"┃ 📄 <b>File:</b> "
            f"<code>{esc(returned_name)}</code>\n"
            f"┃ 📦 <b>Size:</b> "
            f"<b>{esc(returned_size)}</b>\n"
            "┃\n"
            "┃ ☁️ <b>Host:</b> Gofile\n"
            "┃ ⚡ <b>Transfer:</b> "
            "ZTGP2 / MTProto\n"
            "┃\n"
            "┃ 🔗 <b>Download:</b>\n"
            f"┃ <code>{esc(download_url)}</code>\n"
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
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )

        except Exception as error:

            print(
                "[URL] Success message error: "
                f"{error}"
            )

        # ----------------------------------------------------
        # CLEAR REQUEST
        # ----------------------------------------------------

        context.user_data.pop(
            "pending_upload",
            None,
        )

    # ========================================================
    # TIMEOUT
    # ========================================================

    except asyncio.TimeoutError:

        context.user_data.pop(
            "pending_upload",
            None,
        )

        try:

            await query.edit_message_text(
                "❌ <b>TRANSFER TIMEOUT</b>\n\n"
                f"📄 <b>File:</b> "
                f"<code>{esc(file_name)}</code>\n"
                f"📦 <b>Size:</b> "
                f"{esc(format_size(file_size))}\n\n"
                "ZTGP2 did not finish the transfer "
                "within the available time.\n\n"
                "Please try again.",
                parse_mode="HTML",
            )

        except Exception:
            pass

    # ========================================================
    # UNKNOWN ERROR
    # ========================================================

    except Exception as error:

        print(
            "[URL] Unexpected transfer error: "
            f"{error}"
        )

        context.user_data.pop(
            "pending_upload",
            None,
        )

        try:

            await query.edit_message_text(
                "❌ <b>UPLOAD FAILED</b>\n\n"
                f"<code>"
                f"{esc(str(error)[:1500])}"
                f"</code>",
                parse_mode="HTML",
            )

        except Exception as edit_error:

            print(
                "[URL] Error message edit failed: "
                f"{edit_error}"
            )


# ============================================================
# HANDLER REGISTRATION
# ============================================================

def register_handlers(
    application,
):
    """
    Callback routing is handled centrally by main.py.

    Do NOT register another catch-all
    CallbackQueryHandler here.

    main.py already routes:

        url_confirm_upload
        url_cancel_upload

    to button_callback().
    """

    return
    
    