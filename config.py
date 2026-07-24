import os

# Telegram API Credentials
API_ID = int(os.getenv("API_ID", "1234567"))
API_HASH = os.getenv("API_HASH", "your_api_hash_here")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")

# AnimeSalt API Base Endpoint
ANIMESALT_API_URL = os.getenv("ANIMESALT_API_URL", "https://animesalt-api-nine.vercel.app/")

# Custom Rename & Upload Formatting
RENAME_FORMAT = os.getenv("RENAME_FORMAT", "[S{season}-E{episode}] {title} [{quality}] [{audio}] @Anime_Rage_official.mp4")

# Custom Caption Formatting
CAPTION_FORMAT = os.getenv(
    "CAPTION_FORMAT",
    (
        "🎬 **Title:** `{title}`\n"
        "📺 **Season:** `{season}` | 🔢 **Episode:** `{episode}`\n"
        "⚙️ **Quality:** `{quality}` | 🔊 **Audio:** `{audio}`\n"
        "📝 **Overview:** _{synopsis}_\n\n"
        "@Anime_Rage_official"
    )
)
