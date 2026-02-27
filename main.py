import discord
from discord.ext import commands
import os
import asyncio
from config import TOKEN, PREFIX, ACCENT_COLOR

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            activity=discord.Activity(type=discord.ActivityType.listening, name=f"{PREFIX}play"),
            help_command=None
        )

    async def setup_hook(self):
        try:
            await self.load_extension("music_cog")
            print("Music cog loaded successfully.")
        except Exception as e:
            print(f"Failed to load music cog: {e}")
        
        # Sync slash commands
        await self.tree.sync()
        print("Slash commands synced.")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

bot = MusicBot()

@bot.hybrid_command(name="ping", description="Ping the bot")
async def ping(ctx):
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: `{round(bot.latency * 1000)}ms`",
        color=ACCENT_COLOR
    )
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Please set your DISCORD_TOKEN in config.py or as an environment variable.")
    else:
        bot.run(TOKEN)
