"""
Hi Command - Say hello to the bot
"""

import time

COMMAND_NAME = "hi"
ALIASES = ["hello", "hey"]
DESCRIPTION = "Say hello to the bot"
ADMIN_ONLY = False
OWNER_ONLY = False
GROUP_ONLY = False
BOT_ADMIN_NEEDED = False


async def execute(update, context, args, extra):
    # Works for both /hi and menu button

    if update:
        user = update.effective_user
        bot_username = context.bot.username

        async def send(text):
            await update.message.reply_text(text, parse_mode="HTML")

    else:
        user_id = extra["user_id"]
        user_name = extra["user_name"]

        class FakeUser:
            id = user_id
            first_name = user_name
            username = None

        user = FakeUser()
        bot_username = context.bot.username

        async def send(text):
            await context.bot.send_message(
                chat_id=extra["chat_id"],
                text=text,
                parse_mode="HTML"
            )

    hour = time.localtime().tm_hour

    if 5 <= hour < 12:
        greeting = "Good Morning"
    elif 12 <= hour < 17:
        greeting = "Good Afternoon"
    elif 17 <= hour < 21:
        greeting = "Good Evening"
    else:
        greeting = "Good Night"

    mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

    if args:
        name = " ".join(args)
    else:
        name = mention

    text = f"""❖ ── ✦ ──
『✙ 👋 {greeting}, {name}! ✙』

ɪ'ᴍ 🄳🄴🅅 🅉🄸🄺🄺🅈 🄼🄳 😊
── ✦ ── ❖

💫 Bot Info:
• Bot: @{bot_username}
🌟 Need help? Use /menu to see all commands
"""

    await send(text)
    