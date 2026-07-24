import os
import aiohttp
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import config
from api import fetch_anime_data

ADMIN_IDS = [123456789]  # Replace with actual admin Telegram IDs

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
    "animesalt_advanced_bot",
    api_id=runtime_config["API_ID"],
    api_hash=runtime_config["API_HASH"],
    bot_token=runtime_config["BOT_TOKEN"]
)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

HELP_TEXT = (
    "📖 **AnimeSalt Bot Help & Command Guide:**\n\n"
    "🚀 **General Commands:**\n"
    "• /start - Start the bot and view access level\n"
    "• /settings - Open interactive configuration & config editing menu\n"
    "• /help - Display this command guide\n"
    "• /remthumb - Remove your custom thumbnail\n\n"
    "👑 **Admin Commands:**\n"
    "• /admin_panel - Open admin control center\n"
    "• /setconfig <KEY> <VALUE> - Live modify bot configuration variables"
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
            [InlineKeyboardButton("🔑 Edit Bot Token", callback_data="edit_BOT_TOKEN")],
            [InlineKeyboardButton("🆔 Edit API ID & Hash", callback_data="edit_API_CREDENTIALS")],
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
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="open_settings"),
         InlineKeyboardButton("📖 Help", callback_data="show_help")]
    ])
    
    await message.reply_text(
        f"👋 **Welcome to AnimeSalt Bot!**\n\n"
        f"Your current access level: {mode_str}\n"
        "Send me an anime search query or link. Send a photo to set your custom thumbnail.",
        reply_markup=keyboard
    )

@app.on_message(filters.command("settings") & filters.private)
async def settings_command(client: Client, message: Message):
    user_id = message.from_user.id
    if is_admin(user_id):
        await message.reply_text(
            "⚙️ **Admin Configuration Settings Panel:**\n\n"
            "Select a configuration parameter below to edit live:",
            reply_markup=get_settings_keyboard(user_id)
        )
    else:
        await message.reply_text(
            "⚙️ **Interactive Bot Settings Menu:**\n\n"
            "Manage your personal configurations and preferences below:",
            reply_markup=get_settings_keyboard(user_id)
        )

@app.on_callback_query(filters.regex("open_settings"))
async def callback_open_settings(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    title_text = "⚙️ **Admin Configuration Settings Panel:**\n\nSelect a configuration parameter below to edit live:" if is_admin(user_id) else "⚙️ **Interactive Bot Settings Menu:**\n\nManage your personal configurations and preferences below:"
    await callback_query.answer()
    await callback_query.message.edit_text(title_text, reply_markup=get_settings_keyboard(user_id))

@app.on_callback_query(filters.regex("view_config"))
async def callback_view_config(client: Client, callback_query: CallbackQuery):
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("Unauthorized", show_alert=True)
        return
    
    config_summary = (
        "📊 **Current Live Configuration:**\n\n"
        f"• **BOT_TOKEN:** `{runtime_config['BOT_TOKEN'][:10]}...`\n"
        f"• **API_ID:** `{runtime_config['API_ID']}`\n"
        f"• **API_HASH:** `{runtime_config['API_HASH'][:8]}...`\n"
        f"• **API URL:** `{runtime_config['ANIMESALT_API_URL']}`\n"
        f"• **Rename Format:** `{runtime_config['RENAME_FORMAT']}`\n"
        f"• **Caption Format:** `{runtime_config['CAPTION_FORMAT'][:50]}...`"
    )
    await callback_query.answer()
    await callback_query.message.edit_text(
        config_summary,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Settings", callback_data="open_settings")]])
    )

@app.on_callback_query(filters.regex("^edit_"))
async def callback_edit_prompt(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if not is_admin(user_id):
        await callback_query.answer("Admin access required.", show_alert=True)
        return
    
    key = callback_query.data.replace("edit_", "")
    
    if key == "API_CREDENTIALS":
        await callback_query.answer()
        await callback_query.message.reply_text(
            "✏️ **Update API Credentials**\n\n"
            "Please send new values using:\n"
            "`/setconfig API_ID <new_id>`\n"
            "or\n"
            "`/setconfig API_HASH <new_hash>`"
        )
    else:
        await callback_query.answer()
        await callback_query.message.reply_text(
            f"✏️ **Update {key}**\n\n"
            f"Current value: `{runtime_config.get(key, 'N/A')}`\n\n"
            f"Send the new value using:\n"
            f"`/setconfig {key} <new_value>`"
        )

@app.on_message(filters.command("setconfig") & filters.private)
async def set_config_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.reply_text("❌ **Access Denied:** Admin privileges required.")
        return
    
    args = message.command
    if len(args) < 3:
        await message.reply_text(
            "❌ **Invalid usage.**\n"
            "Format: `/setconfig <KEY> <NEW_VALUE>`\n"
            "Example: `/setconfig RENAME_FORMAT [S{season}-E{episode}] {title}.mp4`"
        )
        return
    
    key = args[1]
    new_value = " ".join(args[2:])
    
    if key not in runtime_config:
        await message.reply_text(f"❌ Unknown config key: `{key}`.")
        return
    
    if key == "API_ID":
        try:
            new_value = int(new_value)
        except ValueError:
            await message.reply_text("❌ API_ID must be an integer number.")
            return

    runtime_config[key] = new_value
    await message.reply_text(f"✅ **Configuration successfully updated!**\n`{key}` = `{new_value}`")

@app.on_callback_query(filters.regex("toggle_meta"))
async def callback_toggle_meta(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    current_status = user_metadata_settings.get(user_id, True)
    user_metadata_settings[user_id] = not current_status
    await callback_query.answer("Metadata status updated!")
    await callback_query.message.edit_reply_markup(reply_markup=get_settings_keyboard(user_id))

@app.on_callback_query(filters.regex("info_thumb"))
async def callback_info_thumb(client: Client, callback_query: CallbackQuery):
    await callback_query.answer("Send any photo in chat to save it as your custom thumbnail!", show_alert=True)

@app.on_callback_query(filters.regex("remove_thumb"))
async def callback_remove_thumb(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in user_thumbnails and os.path.exists(user_thumbnails[user_id]):
        os.remove(user_thumbnails[user_id])
        del user_thumbnails[user_id]
        await callback_query.answer("Custom thumbnail removed successfully!")
    else:
        await callback_query.answer("No custom thumbnail found to remove.", show_alert=True)
    await callback_query.message.edit_reply_markup(reply_markup=get_settings_keyboard(user_id))

@app.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    await message.reply_text(HELP_TEXT)

@app.on_callback_query(filters.regex("show_help"))
async def callback_help(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text(
        HELP_TEXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Start", callback_data="back_start")]
        ])
    )

@app.on_callback_query(filters.regex("back_start"))
async def callback_back_start(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    mode_str = "👑 **Admin Mode**" if is_admin(user_id) else "👤 **User Mode**"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="open_settings"),
         InlineKeyboardButton("📖 Help", callback_data="show_help")]
    ])
    
    await callback_query.answer()
    await callback_query.message.edit_text(
        f"👋 **Welcome to AnimeSalt Bot!**\n\n"
        f"Your current access level: {mode_str}\n"
        "Send me an anime search query or link. Send a photo to set your custom thumbnail.",
        reply_markup=keyboard
    )

@app.on_message(filters.photo & filters.private)
async def save_custom_thumbnail(client: Client, message: Message):
    user_id = message.from_user.id
    status_msg = await message.reply_text("🖼️ **Saving custom thumbnail...**")
    
    thumb_path = f"./thumb_{user_id}.jpg"
    await client.download_media(message, file_name=thumb_path)
    user_thumbnails[user_id] = thumb_path
    
    await status_msg.edit_text("✅ **Custom thumbnail successfully saved!** Use /settings to manage it.")

@app.on_message(filters.command("remthumb") & filters.private)
async def remove_custom_thumbnail(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in user_thumbnails and os.path.exists(user_thumbnails[user_id]):
        os.remove(user_thumbnails[user_id])
        del user_thumbnails[user_id]
        await message.reply_text("🗑️ **Custom thumbnail removed successfully.**")
    else:
        await message.reply_text("❌ **No custom thumbnail found.**")

@app.on_message(filters.command("admin_panel") & filters.private)
async def admin_panel(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ **Access Denied:** Admin restricted.")
        return
        
    await message.reply_text(
        "👑 **Admin Control Panel:**\n"
        "• Use /settings to edit configuration keys live\n"
        "• Use `/setconfig <KEY> <VALUE>` to update values directly."
    )

@app.on_message(filters.text & filters.private & ~filters.command(["start", "settings", "setconfig", "help", "admin_panel", "remthumb"]))
async def handle_anime_request(client: Client, message: Message):
    user_id = message.from_user.id
    query_or_url = message.text.strip()
    status_msg = await message.reply_text("🔍 **Processing task request pipeline...**")

    try:
        api_search_url = f"{runtime_config['ANIMESALT_API_URL']}/search?q={query_or_url}"
        anime_data = await fetch_anime_data(query_or_url, api_search_url)
    except Exception as err:
        await status_msg.edit_text(f"❌ **Error:** `{str(err)}`")
        return

    safe_title = "".join(c for c in anime_data["title"] if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    
    filename = runtime_config["RENAME_FORMAT"].format(
        season=anime_data["season"],
        episode=anime_data["episode"],
        title=safe_title,
        quality=anime_data["quality"],
        audio=anime_data["audio"]
    )
    download_path = os.path.join(".", filename)

    try:
        await status_msg.edit_text(f"⬇️ **Downloading stream:** `{anime_data['title']}`...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(anime_data["stream_url"]) as file_resp:
                if file_resp.status != 200:
                    await status_msg.edit_text(f"❌ **Download failed.** HTTP Status: `{file_resp.status}`")
                    return
                
                async with aiofiles.open(download_path, mode='wb') as f:
                    async for chunk in file_resp.content.iter_chunked(1024 * 1024):
                        await f.write(chunk)

        await status_msg.edit_text("⬆️ **Uploading to Telegram channel...**")
        
        custom_caption = runtime_config["CAPTION_FORMAT"].format(
            season=anime_data["season"],
            episode=anime_data["episode"],
            title=anime_data["title"],
            quality=anime_data["quality"],
            audio=anime_data["audio"],
            synopsis=anime_data["synopsis"][:150]
        )
        
        thumb = user_thumbnails.get(user_id)
        if thumb and not os.path.exists(thumb):
            thumb = None

        await message.reply_document(
            document=download_path,
            caption=custom_caption,
            thumb=thumb
        )
        
        await status_msg.delete()

    except Exception as exc:
        await status_msg.edit_text(f"❌ **Pipeline Execution Error:** `{str(exc)}`")

    finally:
        if os.path.exists(download_path):
            os.remove(download_path)

if __name__ == "__main__":
    print("AnimeSalt Final Config Bot Engine is starting...")
    app.run()
