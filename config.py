import os

# Telegram API Credentials
API_ID = int(os.getenv("API_ID", "36428426"))
API_HASH = os.getenv("API_HASH", "30cba30aa38699e77ce264365e327528")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8610209411:AAE2_Qn_85IlnoVMZs4Awc7fpW_raJ_Fgyg")

# AnimeSalt API Base Endpoint
ANIMESALT_API_URL = os.getenv("ANIMESALT_API_URL", "https://animesalt-api-lovat.vercel.app")

# Custom Rename & Upload Formatting
RENAME_FORMAT = os.getenv("RENAME_FORMAT", "[S{season}-E{episode}] {title} [{quality}] [{audio}] @Anime_Kyoto")

# Custom Caption Formatting
CAPTION_FORMAT = os.getenv(
    "CAPTION_FORMAT",
    (
        "🎬 **Title:** `{title}`\n"
        "📺 **Season:** `{season}` | 🔢 **Episode:** `{episode}`\n"
        "⚙️ **Quality:** `{quality}` | 🔊 **Audio:** `{audio}`\n"
        "📝 **Overview:** _{synopsis}_\n\n"
        "@Anime_Kyoto"
    )
)
