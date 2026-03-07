import discord
from discord.ext import commands
import asyncio
from config import TOKEN, PREFIXES, ACCENT_COLOR

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states     = True
        super().__init__(
            command_prefix=commands.when_mentioned_or(*PREFIXES),
            intents=intents,
            activity=discord.Activity(type=discord.ActivityType.listening, name="davey play"),
            help_command=None,
        )

    async def setup_hook(self):
        try:
            await self.load_extension("music_cog")
            print("✅ Music cog loaded.")
        except Exception as e:
            print(f"❌ Music cog failed: {e}")
        await self.tree.sync()
        print("✅ Commands synced.")

    async def on_ready(self):
        # ── Tell Discord to leave ALL voice channels (fixes 4017 on restart) ──
        for guild in self.guilds:
            try:
                await guild.change_voice_state(channel=None)
            except Exception:
                pass

        # Clear local music cog state
        cog = self.get_cog("Music")
        if cog:
            cog.current_tracks.clear()
            cog.np_messages.clear()
            cog.track_start.clear()
            cog.queues.clear()

        # Wipe guild-specific slash command duplicates
        for guild in self.guilds:
            try:
                self.tree.clear_commands(guild=guild)
                await self.tree.sync(guild=guild)
            except Exception:
                pass

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  ✦ {self.user} is online!")
        print(f"  ✦ Guilds: {len(self.guilds)}")
        print("  ✦ Voice sessions cleared!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound): return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"missing argument: `{error.param.name}`")

bot = MusicBot()

@bot.hybrid_command(name="ping", description="Ping the bot")
async def ping(ctx):
    await ctx.send(embed=discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: `{round(bot.latency * 1000)}ms`",
        color=ACCENT_COLOR))

if __name__ == "__main__":
    bot.run(TOKEN)
