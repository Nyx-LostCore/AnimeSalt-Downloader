from __future__ import annotations

import os
import tempfile
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from scraper import AnimexClient

TOKEN = "8565483914:AAGKM6F0lMsFKV1WHg4bh66iamhJJX-00vc"
bot = telebot.TeleBot(TOKEN)
client = AnimexClient()

# In-memory storage for owner configurations (keyed by chat_id)
# Defaults can be customized per user/owner session
OWNER_CONFIGS: dict[int, dict[str, str]] = {}

def get_config(chat_id: int) -> dict[str, str]:
    if chat_id not in OWNER_CONFIGS:
        OWNER_CONFIGS[chat_id] = {
            "naming_format": "{title} - S01E{ep:02d} [{quality}].mp4",
            "metadata_title": "{title} - Episode {ep}",
            "metadata_show": "{title}",
            "custom_thumb_url": ""
        }
    return OWNER_CONFIGS[chat_id]

def download_file(url: str, output_path: str) -> None:
    """Download file using curl_cffi session stream."""
    with client.session.stream("GET", url, timeout=30.0) as resp:
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

def download_thumbnail(image_url: str, output_path: str) -> bool:
    """Download cover image or custom thumb URL for thumbnail usage."""
    try:
        resp = client.session.get(image_url, timeout=10.0)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception:
        pass
    return False

def process_media(
    input_video: str,
    output_video: str,
    thumb_path: str | None,
    metadata: dict[str, str],
) -> None:
    """Embeds metadata and safely attaches a thumbnail using ffmpeg."""
    import subprocess
    import os

    # Check if input video exists and is not empty
    if not os.path.exists(input_video) or os.path.getsize(input_video) == 0:
        raise RuntimeError("Download failed: The raw video file is empty or missing.")

    cmd = ["ffmpeg", "-y", "-i", input_video]
    
    has_valid_thumb = thumb_path and os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0

    if has_valid_thumb:
        cmd.extend([
            "-i", thumb_path,
            "-map", "0:v", "-map", "0:a?", "-map", "1:v",
            "-c:v", "copy", "-c:a", "copy",
            "-disposition:v:1", "attached_pic"
        ])
    else:
        cmd.extend(["-c", "copy"])

    for key, val in metadata.items():
        cmd.extend(["-metadata", f"{key}={val}"])

    cmd.append(output_video)

    # Run and capture errors cleanly
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        error_message = result.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"FFmpeg failed (Exit code {result.returncode}): {error_message}")


HELP_TEXT = (
    "📖 **Anime DL Bot Help & Instructions**\n\n"
    "⚙️ **Available Commands:**\n"
    "• /start - Launch the main dashboard & settings\n"
    "• /help - View this help menu\n"
    "• `/dl <anime name> | <episode>` - Download & process episode\n"
    "• `/setformat <pattern>` - Set custom filename format\n"
    "• `/setmeta <title_tag> | <show_tag>` - Set custom metadata tags\n"
    "• `/setthumb <image_url>` - Set a custom thumbnail image URL\n"
    "• /settings - View your current custom configurations"
)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("❓ Help & Commands", callback_data="show_help"),
        InlineKeyboardButton("⚙️ View Settings", callback_data="show_settings")
    )
    
    bot.send_message(
        message.chat.id,
        "👋 **Welcome to the Configurable Anime DL Bot!**\n\n"
        "You can customize file naming formats, metadata tags, and custom thumbnails live using bot commands or buttons below.",
        reply_markup=markup,
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["help"])
def send_help_command(message):
    bot.reply_to(message, HELP_TEXT, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data in ["show_help", "show_settings"])
def callback_handler(call):
    bot.answer_callback_query(call.id)
    config = get_config(call.message.chat.id)
    
    if call.data == "show_help":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=HELP_TEXT,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back to Settings", callback_data="show_settings"))
        )
    elif call.data == "show_settings":
        settings_text = (
            "⚙️ **Your Current Configuration:**\n\n"
            f"• **Naming Format:** `{config['naming_format']}`\n"
            f"• **Meta Title Tag:** `{config['metadata_title']}`\n"
            f"• **Meta Show Tag:** `{config['metadata_show']}`\n"
            f"• **Custom Thumbnail URL:** `{config['custom_thumb_url'] or 'None (Using Auto Cover)'}`\n\n"
            "Use `/setformat`, `/setmeta`, or `/setthumb` to update these values."
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=settings_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("❓ Help Menu", callback_data="show_help"))
        )


@bot.message_handler(commands=["setformat"])
def handle_set_format(message):
    args = message.text.replace("/setformat", "").strip()
    if not args:
        bot.reply_to(message, "⚠️ Usage: `/setformat {title} - S01E{ep:02d} [{quality}].mp4`", parse_mode="Markdown")
        return
    
    config = get_config(message.chat.id)
    config["naming_format"] = args
    bot.reply_to(message, f"✅ Naming format updated successfully to:\n`{args}`", parse_mode="Markdown")


@bot.message_handler(commands=["setmeta"])
def handle_set_meta(message):
    args = message.text.replace("/setmeta", "").strip()
    if "|" not in args:
        bot.reply_to(message, "⚠️ Usage: `/setmeta <title_tag> | <show_tag>`", parse_mode="Markdown")
        return
    
    title_tag, show_tag = [x.strip() for x in args.split("|", 1)]
    config = get_config(message.chat.id)
    config["metadata_title"] = title_tag
    config["metadata_show"] = show_tag
    bot.reply_to(message, f"✅ Metadata updated successfully!\n• Title Tag: `{title_tag}`\n• Show Tag: `{show_tag}`", parse_mode="Markdown")


@bot.message_handler(commands=["setthumb"])
def handle_set_thumb(message):
    args = message.text.replace("/setthumb", "").strip()
    if not args:
        bot.reply_to(message, "⚠️ Usage: `/setthumb <direct_image_url>` (Pass 'clear' to reset)", parse_mode="Markdown")
        return
    
    config = get_config(message.chat.id)
    if args.lower() == "clear":
        config["custom_thumb_url"] = ""
        bot.reply_to(message, "✅ Custom thumbnail cleared. Will use default anime cover image.")
    else:
        config["custom_thumb_url"] = args
        bot.reply_to(message, f"✅ Custom thumbnail URL updated successfully:\n`{args}`", parse_mode="Markdown")


@bot.message_handler(commands=["settings"])
def handle_view_settings(message):
    config = get_config(message.chat.id)
    settings_text = (
        "⚙️ **Your Current Configuration:**\n\n"
        f"• **Naming Format:** `{config['naming_format']}`\n"
        f"• **Meta Title Tag:** `{config['metadata_title']}`\n"
        f"• **Meta Show Tag:** `{config['metadata_show']}`\n"
        f"• **Custom Thumbnail URL:** `{config['custom_thumb_url'] or 'None (Using Auto Cover)'}`"
    )
    bot.reply_to(message, settings_text, parse_mode="Markdown")


@bot.message_handler(commands=["dl"])
def handle_download(message):
    args = message.text.replace("/dl", "").strip()
    if "|" not in args:
        bot.reply_to(message, "⚠️ Format error! Use: `/dl Anime Name | Episode Number`", parse_mode="Markdown")
        return

    query, ep_str = [x.strip() for x in args.split("|", 1)]
    try:
        ep_num = int(ep_str)
    except ValueError:
        bot.reply_to(message, "⚠️ Episode number must be a valid integer.")
        return

    config = get_config(message.chat.id)
    status_msg = bot.reply_to(message, f"🔍 Searching for *{query}* (Ep {ep_num})...", parse_mode="Markdown")

    try:
        results = client.search(query, limit=1)
        if not results:
            bot.edit_message_text("❌ Anime not found.", chat_id=message.chat.id, message_id=status_msg.message_id)
            return

        anime = results[0]
        anime_id = anime["id"]
        title = anime.get("titleEnglish") or anime.get("titleRomaji") or "Unknown Title"
        cover_image = anime.get("coverImage")

        bot.edit_message_text(f"📥 Found: *{title}*\nFetching stream sources...", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")

        best_source = client.get_best_source(anime_id, ep_num=ep_num, type_="sub")
        if not best_source or not best_source.get("url"):
            bot.edit_message_text(f"❌ No valid stream sources found for Episode {ep_num}.", chat_id=message.chat.id, message_id=status_msg.message_id)
            return

        video_url = best_source["url"]
        quality = best_source.get("quality", "1080p")

        bot.edit_message_text(f"⬇️ Downloading *{title}* [Ep {ep_num}] [{quality}]...", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")

        with tempfile.TemporaryDirectory() as tmpdir:
            raw_path = os.path.join(tmpdir, "raw.mp4")
            thumb_path = os.path.join(tmpdir, "thumb.jpg")
            
            # Apply user-defined format configuration
            formatted_filename = config["naming_format"].format(
                title=title.replace("/", "_"),
                ep=ep_num,
                quality=quality
            )
            final_path = os.path.join(tmpdir, formatted_filename)

            has_thumb = False
            target_thumb_url = config["custom_thumb_url"] or cover_image
            if target_thumb_url:
                has_thumb = download_thumbnail(target_thumb_url, thumb_path)

            download_file(video_url, raw_path)

            bot.edit_message_text(f"⚙️ Processing metadata & thumbnail via ffmpeg...", chat_id=message.chat.id, message_id=status_msg.message_id)
            
            # Apply custom metadata configurations
            fmt_vars = {"title": title, "ep": ep_num, "quality": quality}
            metadata = {
                "title": config["metadata_title"].format(**fmt_vars),
                "show": config["metadata_show"].format(**fmt_vars),
                "episode_id": str(ep_num),
            }

            process_media(
                input_video=raw_path,
                output_video=final_path,
                thumb_path=thumb_path if has_thumb else None,
                metadata=metadata
            )

            bot.edit_message_text(f"🚀 Uploading to Telegram...", chat_id=message.chat.id, message_id=status_msg.message_id)

            with open(final_path, "rb") as vid:
                bot.send_video(
                    chat_id=message.chat.id,
                    video=vid,
                    caption=f"✨ *{title}* - Episode {ep_num} ({quality})",
                    parse_mode="Markdown",
                    supports_streaming=True,
                    thumbnail=open(thumb_path, "rb") if has_thumb else None
                )

            bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"⚠️ An error occurred: {str(e)}", chat_id=message.chat.id, message_id=status_msg.message_id)


if __name__ == "__main__":
    print("Bot is up and running...")
    bot.infinity_polling()
