import os

# Bot configuration
TOKEN = os.getenv("DISCORD_TOKEN", "MTQ1MzM5OTI3MzU1MDEyMzA1MA.Gg4ObN.syoRTybgXt_NXTgs7kJ2-qw9aTeCWidUURIp_w")
PREFIX = "!"

# Aesthetic settings
EMBED_COLOR = 0x2b2d31 # Dark grey aesthetic
ACCENT_COLOR = 0x7289da # Discord blurple or any aesthetic color
SUCCESS_COLOR = 0x2ecc71
ERROR_COLOR = 0xe74c3c

# FFmpeg options
FFMPEG_EXECUTABLE = os.getenv("FFMPEG_PATH", "ffmpeg") # Default to PATH, or provide direct path
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

# YDL options
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}
