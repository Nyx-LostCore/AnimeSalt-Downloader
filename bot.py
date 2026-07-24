import os
import aiohttp
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import config
from api import fetch_anime_data

ADMIN_IDS = [123456789]

user_metadata_settings = {}
user_thumbnails = {}

runtime_config = {
    "BOT_TOKEN": config.BOT_TOKEN,
    "API_ID": config.API_ID,
    "API_HASH": config.API_HASH,
    "ANIMESALT_API_URL": config.ANIMESALT_API_URL,
    "RENAME_FORMAT": config.RENAME_FORMAT,
    "CAPTION_FORMAT": config.CAPTION_FORMAT
}

app = Client(
    "animesalt_bot_session",
    api_id=runtime_config["API_ID"],
    api_hash=runtime_config["API_HASH"],
    bot_token=runtime_config["BOT_TOKEN"]
)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

HELP_TEXT = (
    "📖 **AnimeSalt Bot Help & Command Guide:**\n\n"
    "• /start - Start the bot\n"
    "• /settings - Open configuration menu\n"
    "• /help - Display this command guide\n"
    "• /remthumb - Remove custom thumbnail"
)

def get_settings_keyboard(user_id: int):
    if not is_admin(user_id):
        meta_status = "ENABLED ✅" if user_metadata_settings.get(user_id, True) else "DISABLED ❌"
        has_thumb = "Yes 🖼️" if user_id in user_thumbnails and os.path.exists(user_thumbnails[user_id]) else "No ❌"
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Toggle Metadata: {meta_status}", callback_data="toggle_meta")],
            [InlineKeyboardButton(f"Custom Thumbnail Set: {has_thumb}", callback_data="info_thumb")],
            [InlineKeyboardButton("🗑️ Remove Thumbnail", callback_data="remove_thumb")],
            [InlineKeyboardButton("🔙 Back to Start", callback_data="back_start")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Edit API Endpoint", callback_data="edit_ANIMESALT_API_URL")],
            [InlineKeyboardButton("📝 Edit Rename Format", callback_data="edit_RENAME_FORMAT")],
            [InlineKeyboardButton("💬 Edit Caption Format", callback_data="edit_CAPTION_FORMAT")],
            [InlineKeyboardButton("📊 View Current Config", callback_data="view_config")],
            [InlineKeyboardButton("🔙 Back to Start", callback_data="back_start")]
        ])

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    mode_str = "👑 **Admin Mode**" if is_admin(user_id) else "👤 **User Mode**"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Settings", callback_data="open_settings"), InlineKeyboardButton("📖 Help", callback_data="show_help")]])
    await message.reply_text(f"👋 **Welcome to AnimeSalt Bot!**\n\nAccess level: {mode_str}\nSend me an anime search query or link.", reply_markup=keyboard)

@app.on_message(filters.command("settings") & filters.private)
async def settings_command(client: Client, message: Message):
    await message.reply_text("⚙️ **Settings Menu:**", reply_markup=get_settings_keyboard(message.from_user.id))

@app.on_callback_query(filters.regex("open_settings"))
async def callback_open_settings(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("⚙️ **Settings Menu:**", reply_markup=get_settings_keyboard(callback_query.from_user.id))

@app.on_callback_query(filters.regex("view_config"))
async def callback_view_config(client: Client, callback_query: CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("Unauthorized", show_alert=True)
    cfg_summary = f"📊 **Config:**\n• URL: `{runtime_config['ANIMESALT_API_URL']}`\n• Rename: `{runtime_config['RENAME_FORMAT']}`"
    await callback_query.answer()
    await callback_query.message.edit_text(cfg_summary, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="open_settings")]]))

@app.on_callback_query(filters.regex("^edit_"))
async def callback_edit_prompt(client: Client, callback_query: CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        return await callback_query.answer("Admin only.", show_alert=True)
    key = callback_query.data.replace("edit_", "")
    await callback_query.answer()
    await callback_query.message.reply_text(f"✏️ Send new value using:\n`/setconfig {key} <new_value>`")

@app.on_message(filters.command("setconfig") & filters.private)
async def set_config_command(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply_text("❌ Access Denied.")
    args = message.command
    if len(args) < 3:
        return await message.reply_text("❌ Format: `/setconfig <KEY> <NEW_VALUE>`")
    key, val = args[1], " ".join(args[2:])
    if key not in runtime_config:
        return await message.reply_text(f"❌ Unknown key: `{key}`")
    runtime_config[key] = val
    await message.reply_text(f"✅ Updated `{key}` = `{val}`")

@app.on_callback_query(filters.regex("toggle_meta"))
async def callback_toggle_meta(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_metadata_settings[user_id] = not user_metadata_settings.get(user_id, True)
    await callback_query.answer("Updated!")
    await callback_query.message.edit_reply_markup(reply_markup=get_settings_keyboard(user_id))

@app.on_callback_query(filters.regex("remove_thumb"))
async def callback_remove_thumb(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in user_thumbnails and os.path.exists(user_thumbnails[user_id]):
        os.remove(user_thumbnails[user_id])
        del user_thumbnails[user_id]
        await callback_query.answer("Thumbnail removed!")
    else:
        await callback_query.answer("No thumbnail found.", show_alert=True)
    await callback_query.message.edit_reply_markup(reply_markup=get_settings_keyboard(user_id))

@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    await message.reply_text(HELP_TEXT)

@app.on_message(filters.photo & filters.private)
async def save_custom_thumbnail(client: Client, message: Message):
    status = await message.reply_text("🖼️ Saving thumbnail...")
    path = f"./thumb_{message.from_user.id}.jpg"
    await client.download_media(message, file_name=path)
    user_thumbnails[message.from_user.id] = path
    await status.edit_text("✅ Thumbnail saved successfully!")

@app.on_message(filters.text & filters.private & ~filters.command(["start", "settings", "setconfig", "help", "remthumb"]))
async def handle_anime_request(client: Client, message: Message):
    status_msg = await message.reply_text("🔍 Searching anime via API...")
    try:
        anime_data = await fetch_anime_data(message.text.strip(), runtime_config["ANIMESALT_API_URL"])
    except Exception as err:
        return await status_msg.edit_text(f"❌ Error: `{str(err)}`")

    safe_title = "".join(c for c in anime_data["title"] if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    filename = runtime_config["RENAME_FORMAT"].format(
        season=anime_data["season"], episode=anime_data["episode"],
        title=safe_title, quality=anime_data["quality"], audio=anime_data["audio"]
    )
    download_path = os.path.join(".", filename)

    try:
        await status_msg.edit_text(f"⬇️ Downloading: `{anime_data['title']}`...")
        async with aiohttp.ClientSession() as session:
            async with session.get(anime_data["stream_url"]) as file_resp:
                if file_resp.status != 200:
                    return await status_msg.edit_text(f"❌ Download failed. HTTP Status: {file_resp.status}")
                async with aiofiles.open(download_path, 'wb') as f:
                    async for chunk in file_resp.content.iter_chunked(1024 * 1024):
                        await f.write(chunk)

        await status_msg.edit_text("⬆️ Uploading file to Telegram...")
        caption = runtime_config["CAPTION_FORMAT"].format(
            season=anime_data["season"], episode=anime_data["episode"],
            title=anime_data["title"], quality=anime_data["quality"],
            audio=anime_data["audio"], synopsis=anime_data["synopsis"][:150]
        )
        thumb = user_thumbnails.get(message.from_user.id)
        if thumb and not os.path.exists(thumb):
            thumb = None

        await message.reply_document(document=download_path, caption=caption, thumb=thumb)
        await status_msg.delete()
    except Exception as exc:
        await status_msg.edit_text(f"❌ Pipeline Error: `{str(exc)}`")
    finally:
        if os.path.exists(download_path):
            os.remove(download_path)

if __name__ == "__main__":
    print("Bot is starting...")
    app.run()
