import discord
import yt_dlp
import asyncio
import requests
from bs4 import BeautifulSoup
from config import YDL_OPTIONS, EMBED_COLOR, ACCENT_COLOR, FFMPEG_EXECUTABLE

ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.thumbnail = data.get('thumbnail')
        self.duration = data.get('duration')
        self.requester = data.get('requester')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, requester=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        data['requester'] = requester
        
        # Explicitly check for ffmpeg if possible, but discord.py usually looks in PATH
        # We'll use a try-except in the cog to catch the error and provide a better message
        executable = FFMPEG_EXECUTABLE # Default to PATH
        
        return cls(discord.FFmpegPCMAudio(filename, executable=executable, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn"), data=data)

def create_aesthetic_embed(title=None, description=None, color=EMBED_COLOR, thumbnail=None, footer=None, fields=None):
    embed = discord.Embed(title=title, description=description, color=color)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if footer:
        embed.set_footer(text=footer)
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    return embed

def format_duration(seconds):
    if not seconds:
        return "Unknown"
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def create_now_playing_embed(track):
    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"**[{track.title}]({track.url})**",
        color=ACCENT_COLOR
    )
    embed.set_thumbnail(url=track.thumbnail)
    embed.add_field(name="Duration", value=format_duration(track.duration), inline=True)
    embed.add_field(name="Requested by", value=track.requester.mention, inline=True)
    embed.set_footer(text="Aesthetic Music Bot • Playing high quality audio")
    return embed

async def get_lyrics(song_name):
    # Simplified search on Google or Genius (mock/simplified for example)
    # In a real bot, use a dedicated API like Genius
    search_url = f"https://www.google.com/search?q={song_name.replace(' ', '+')}+lyrics"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Note: Scraping Google directly is fragile, but for a bot example it's common
        # A better way is using Genius API
        return f"Lyrics search results for: **{song_name}**\n(Consider using Genius API for full lyrics integration)"
    except:
        return "Could not find lyrics."
