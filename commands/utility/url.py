"""
URL Command - Download and upload files using Gofile API
Supports: Images, Audio, Video, Documents, Stickers (static + animated)
"""

import os
import re
import json
import time
import random
import asyncio
import aiohttp
import aiofiles
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from pathlib import Path
import requests

COMMAND_NAME = 'url'
ALIASES = ['gofile', 'upload', 'download']
DESCRIPTION = 'Download and upload files using Gofile API'
ADMIN_ONLY = False
OWNER_ONLY = False
GROUP_ONLY = False
BOT_ADMIN_NEEDED = False

# ============================================
# CONSTANTS
# ============================================
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
MAX_AUDIO_SIZE = 80 * 1024 * 1024  # 80MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
MAX_DOCUMENT_SIZE = 1000 * 1024 * 1024  # 1000MB (1GB)
MAX_STICKER_SIZE = 500 * 1024  # 500KB (Telegram sticker limit)

GOFILE_UPLOAD_URL = "https://upload.gofile.io/uploadfile"
TEMP_DIR = Path(__file__).parent.parent.parent / 'tmp'

# Ensure temp directory exists
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# STICKER DETECTION
# ============================================
def is_animated_sticker(sticker):
    """Check if sticker is animated (video/webm)"""
    if hasattr(sticker, 'is_animated'):
        return sticker.is_animated
    if hasattr(sticker, 'is_video'):
        return sticker.is_video
    # Check mime type
    if hasattr(sticker, 'mime_type'):
        return sticker.mime_type in ['video/webm', 'video/mp4']
    return False

def is_static_sticker(sticker):
    """Check if sticker is static (image/webp)"""
    if is_animated_sticker(sticker):
        return False
    if hasattr(sticker, 'mime_type'):
        return sticker.mime_type == 'image/webp'
    return True

# ============================================
# HELPERS
# ============================================
def get_file_type(mime_type, file_name, message):
    """Determine file type based on mime type or extension"""
    
    # Check for stickers first (special handling)
    if message and hasattr(message, 'sticker'):
        if is_animated_sticker(message.sticker):
            return 'video'  # Animated stickers are videos
        else:
            return 'image'  # Static stickers are images
    
    # Image types
    if any(mime_type.startswith(ext) for ext in ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp', 'image/svg']):
        return 'image'
    # Audio types
    if any(mime_type.startswith(ext) for ext in ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/aac', 'audio/flac']):
        return 'audio'
    # Video types
    if any(mime_type.startswith(ext) for ext in ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm', 'video/mpeg']):
        return 'video'
    # Document types
    if any(mime_type.startswith(ext) for ext in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument', 'text/plain', 'application/json', 'application/zip', 'application/x-rar-compressed']):
        return 'document'
    # Check extension as fallback
    ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
    image_ext = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg']
    audio_ext = ['mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a']
    video_ext = ['mp4', 'mov', 'avi', 'webm', 'mkv', 'mpeg']
    if ext in image_ext:
        return 'image'
    if ext in audio_ext:
        return 'audio'
    if ext in video_ext:
        return 'video'
    return 'document'

def get_max_size(file_type):
    """Get max file size for each type"""
    sizes = {
        'image': MAX_IMAGE_SIZE,
        'audio': MAX_AUDIO_SIZE,
        'video': MAX_VIDEO_SIZE,
        'document': MAX_DOCUMENT_SIZE
    }
    return sizes.get(file_type, MAX_DOCUMENT_SIZE)

def format_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def get_file_emoji(file_type):
    """Get emoji for file type"""
    emojis = {
        'image': '🖼️',
        'audio': '🎵',
        'video': '🎬',
        'document': '📄',
        'sticker': '🎨'
    }
    return emojis.get(file_type, '📁')

# ============================================
# GOFILE UPLOAD (FIXED)
# ============================================
async def upload_to_gofile(file_path, folder_id=None):
    """Upload a file to Gofile using the current upload API."""
    try:
        form = aiohttp.FormData()

        # Add the file
        with open(file_path, "rb") as f:
            form.add_field(
                "file",
                f,
                filename=Path(file_path).name,
                content_type="application/octet-stream"
            )

            # Optional folder
            if folder_id:
                form.add_field("folderId", str(folder_id))

            # Upload
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    GOFILE_UPLOAD_URL,
                    data=form
                ) as resp:

                    response_text = await resp.text()

                    print(f"[GOFILE] HTTP Status: {resp.status}")
                    print(f"[GOFILE] Response: {response_text[:1000]}")

                    if resp.status != 200:
                        return None

                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError:
                        print("[GOFILE] Invalid JSON response")
                        return None

                    if result.get("status") == "ok":
                        return result

                    print(f"[GOFILE] Upload failed: {result}")
                    return None

    except Exception as e:
        print(f"[GOFILE] Upload error: {e}")
        return None

# ============================================
# DOWNLOAD FILE FROM TELEGRAM
# ============================================
async def download_file_from_telegram(bot, file_id, file_name=None):
    """Download file from Telegram"""
    try:
        # Create temp file path
        if not file_name:
            file_name = f"file_{int(time.time())}"
        file_path = TEMP_DIR / f"upload_{file_name}_{int(time.time())}"
        
        # Download file
        file = await bot.get_file(file_id)
        await file.download_to_drive(file_path)
        
        return file_path
    except Exception as e:
        print(f"[DOWNLOAD] Error: {e}")
        return None

# ============================================
# MAIN COMMAND
# ============================================
async def execute(update, context, args, extra):
    """Main execute function"""
    
    # Check for callback query (button press)
    if update and update.callback_query:
        await button_callback(update, context)
        return
    
    # Check if replying to a message
    is_reply = False
    reply_message = None
    if update and update.message and update.message.reply_to_message:
        reply_message = update.message.reply_to_message
        is_reply = True
    
    # If no args and no reply, show menu
    if not args and not is_reply:
        await show_menu(update, context, extra)
        return
    
    # If replying to a message, process the file
    if is_reply:
        await handle_reply(update, context, reply_message, extra)
        return
    
    # If args provided, treat as URL or text
    await handle_url(update, context, args, extra)

# ============================================
# SHOW MENU
# ============================================
async def show_menu(update, context, extra):
    """Show the main menu"""
    menu_text = """╭━━━༺ *📦 URL / GOFILE* ༻━━━╮
┃
┃ 🔧 *COMMANDS* :
┃
┃ 📤 *UPLOAD FILE* :
┃ Reply to a file with:
┃ /url
┃
┃ 📥 *DOWNLOAD FROM URL* :
┃ /url <url>
┃
┃ 📋 *SUPPORTED FILES* :
┃ 📸 Images (20MB max)
┃ 🎵 Audio (80MB max)
┃ 🎬 Video (500MB max)
┃ 📄 Documents (1000MB max)
┃ 🎨 Stickers (Static & Animated)
┃
┃ 💡 *EXAMPLES* :
┃ Reply to a file with /url
┃ /url https://example.com/file.mp4
┃
╰━━━━━━━━━━━━━━━━━━╯
> *ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴅᴇᴠ ᴢɪᴋᴋʏ ᴍᴅ*"""
    
    if update:
        await update.message.reply_text(menu_text, parse_mode='Markdown')
    else:
        reply = extra.get('reply')
        if reply:
            await reply(menu_text)

# ============================================
# HANDLE REPLY (FILE UPLOAD)
# ============================================
async def handle_reply(update, context, reply_message, extra):
    """Handle reply to a file message"""
    # Get file info
    file_info = None
    file_type = None
    file_size = 0
    file_name = "file"
    is_sticker = False
    is_animated = False
    
    # Check for different message types
    if reply_message.document:
        file_info = reply_message.document
        file_type = get_file_type(file_info.mime_type, file_info.file_name or "file", reply_message)
        file_size = file_info.file_size
        file_name = file_info.file_name or "file"
    elif reply_message.photo:
        file_info = reply_message.photo[-1]  # Get largest photo
        file_type = 'image'
        file_size = file_info.file_size
        file_name = f"image_{int(time.time())}.jpg"
    elif reply_message.video:
        file_info = reply_message.video
        file_type = 'video'
        file_size = file_info.file_size
        file_name = file_info.file_name or f"video_{int(time.time())}.mp4"
    elif reply_message.audio:
        file_info = reply_message.audio
        file_type = 'audio'
        file_size = file_info.file_size
        file_name = file_info.file_name or f"audio_{int(time.time())}.mp3"
    elif reply_message.voice:
        file_info = reply_message.voice
        file_type = 'audio'
        file_size = file_info.file_size
        file_name = f"voice_{int(time.time())}.ogg"
    elif reply_message.video_note:
        file_info = reply_message.video_note
        file_type = 'video'
        file_size = file_info.file_size
        file_name = f"video_note_{int(time.time())}.mp4"
    elif reply_message.sticker:
        file_info = reply_message.sticker
        is_sticker = True
        is_animated = is_animated_sticker(file_info)
        file_type = 'video' if is_animated else 'image'
        file_size = file_info.file_size
        # Get file name
        if hasattr(file_info, 'file_name') and file_info.file_name:
            file_name = file_info.file_name
        elif is_animated:
            file_name = f"sticker_animated_{int(time.time())}.webm"
        else:
            file_name = f"sticker_{int(time.time())}.webp"
    else:
        await update.message.reply_text(
            "❌ *Unsupported file type*\n\n"
            "Please send a valid file to upload.\n"
            "Supported: Images, Audio, Video, Documents, Stickers"
        )
        return
    
    # Check if it's a sticker (special handling - use document upload for stickers)
    if is_sticker:
        file_type_display = '🎨 Sticker (Animated)' if is_animated else '🎨 Sticker (Static)'
        max_size = MAX_DOCUMENT_SIZE
    else:
        file_type_display = file_type.capitalize()
        max_size = get_max_size(file_type)
    
    # Check file size limit
    if file_size > max_size:
        size_limit = format_size(max_size)
        await update.message.reply_text(
            f"❌ *File too large!*\n\n"
            f"📁 *Type:* {file_type_display}\n"
            f"📦 *Size:* {format_size(file_size)}\n"
            f"📊 *Max allowed:* {size_limit}\n\n"
            f"Please compress or use a smaller file."
        )
        return
    
    # Store file info in context
    context.user_data['pending_upload'] = {
        'file_id': file_info.file_id,
        'file_type': file_type,
        'file_size': file_size,
        'file_name': file_name,
        'mime_type': getattr(file_info, 'mime_type', None),
        'is_sticker': is_sticker,
        'is_animated': is_animated,
        'file_type_display': file_type_display
    }
    
    # Show confirmation buttons
    keyboard = [
        [
            InlineKeyboardButton("📤 Upload", callback_data="confirm_upload"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_upload")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Show file info with confirmation
    sticker_info = " 🎨 (Animated)" if is_animated else " 🎨" if is_sticker else ""
    await update.message.reply_text(
        f"📤 *File detected*{sticker_info}\n\n"
        f"📁 *Type:* {file_type_display}\n"
        f"📦 *Size:* {format_size(file_size)}\n"
        f"📄 *Name:* {file_name}\n\n"
        f"Would you like to upload this file to Gofile?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ============================================
# HANDLE URL (DOWNLOAD FROM URL)
# ============================================
async def handle_url(update, context, args, extra):
    """Handle URL input"""
    url = args[0]
    
    # Validate URL
    if not url.startswith('http://') and not url.startswith('https://'):
        await update.message.reply_text("❌ *Invalid URL*\n\nPlease provide a valid URL starting with http:// or https://")
        return
    
    # Check if it's a Gofile URL (direct upload)
    if 'gofile.io' in url:
        await handle_gofile_url(update, context, url, extra)
        return
    
    # For other URLs, show info
    await update.message.reply_text(
        f"📥 *Processing URL*\n\n"
        f"🔗 {url}\n\n"
        f"⏳ *Fetching file information...*"
    )
    
    # TODO: Implement URL download functionality
    await update.message.reply_text(
        f"⚠️ *URL download*\n\n"
        f"Direct URL download will be available soon.\n\n"
        f"💡 For now, please download the file and send it here, or use a Gofile link."
    )

# ============================================
# HANDLE GOFILE URL
# ============================================
async def handle_gofile_url(update, context, url, extra):
    """Handle Gofile URL (direct download)"""
    # Extract file ID from URL
    file_id = None
    if '/d/' in url:
        file_id = url.split('/d/')[-1].split('/')[0]
    elif '?fileId=' in url:
        file_id = url.split('?fileId=')[-1].split('&')[0]
    
    if not file_id:
        await update.message.reply_text("❌ *Invalid Gofile URL*\n\nCould not extract file ID.")
        return
    
    await update.message.reply_text(
        f"📥 *Gofile URL detected*\n\n"
        f"🔗 File ID: `{file_id}`\n\n"
        f"⏳ *Fetching file...*"
    )
    
    # TODO: Implement Gofile download
    await update.message.reply_text(
        f"⚠️ *Gofile download*\n\n"
        f"Direct Gofile download will be available soon.\n\n"
        f"💡 For now, please download the file manually and send it here."
    )

# ============================================
# BUTTON CALLBACK HANDLER
# ============================================
async def button_callback(update, context):
    """Handle button callbacks"""
    query = update.callback_query
    data = query.data
    
    await query.answer()
    
    if data == "cancel_upload":
        await query.edit_message_text("❌ *Upload cancelled*")
        context.user_data.pop('pending_upload', None)
        return
    
    if data == "confirm_upload":
        # Get pending upload data
        pending = context.user_data.get('pending_upload', {})
        if not pending:
            await query.edit_message_text("❌ *Session expired*\n\nPlease send the file again.")
            return
        
        # Show uploading message
        await query.edit_message_text(
            f"⏳ *Uploading file to Gofile...*\n\n"
            f"📁 *Type:* {pending.get('file_type_display', 'unknown')}\n"
            f"📦 *Size:* {format_size(pending.get('file_size', 0))}\n"
            f"📄 *Name:* {pending.get('file_name', 'file')}\n\n"
            f"Please wait..."
        )
        
        try:
            # Download file from Telegram
            file_path = await download_file_from_telegram(
                query.message.bot,
                pending['file_id'],
                pending.get('file_name', 'file')
            )
            
            if not file_path:
                await query.edit_message_text("❌ *Failed to download file*\n\nPlease try again.")
                return
            
            # Upload to Gofile (no token needed - guest upload)
            result = await upload_to_gofile(file_path)
            
            # Clean up temp file
            try:
                file_path.unlink()
            except:
                pass
            
            if result and result.get('status') == 'ok':
                data = result.get('data', {})
                download_page = data.get('downloadPage')
                file_name = data.get('fileName', pending.get('file_name', 'file'))
                file_id = data.get('fileId')
                
                await query.edit_message_text(
                    f"✅ *Upload Successful!*\n\n"
                    f"📄 *File:* {file_name}\n"
                    f"📦 *Size:* {format_size(pending.get('file_size', 0))}\n"
                    f"🔗 *Link:* {download_page}\n\n"
                    f"💡 The file is now available at the link above."
                )
            else:
                error_msg = result.get('message', 'Unknown error') if result else 'No response'
                await query.edit_message_text(
                    f"❌ *Upload Failed*\n\n"
                    f"Could not upload to Gofile.\n"
                    f"Error: {error_msg}\n\n"
                    f"Please try again later."
                )
                
        except Exception as e:
            print(f"[UPLOAD] Error: {e}")
            await query.edit_message_text(
                f"❌ *Upload Failed*\n\n"
                f"Error: {str(e)[:100]}\n\n"
                f"Please try again later."
            )
        
        # Clear pending data
        context.user_data.pop('pending_upload', None)
        return

# ============================================
# REGISTER HANDLERS
# ============================================
def register_handlers(application):
    """Register callback query handler"""
    application.add_handler(CallbackQueryHandler(button_callback))
    
    