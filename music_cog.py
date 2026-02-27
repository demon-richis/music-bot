import discord
from discord.ext import commands
import asyncio
import random
from utils import YTDLSource, create_aesthetic_embed, create_now_playing_embed, format_duration, get_lyrics
from config import ACCENT_COLOR, ERROR_COLOR

class MusicView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    @discord.ui.button(label="⏯️", style=discord.ButtonStyle.grey)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc: return
        if vc.is_paused():
            vc.resume()
            await interaction.response.send_message("Resumed!", ephemeral=True)
        elif vc.is_playing():
            vc.pause()
            await interaction.response.send_message("Paused!", ephemeral=True)

    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.grey)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await interaction.response.send_message("Skipped!", ephemeral=True)

    @discord.ui.button(label="⏹️", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("Stopped and disconnected!", ephemeral=True)

    @discord.ui.button(label="📜 Queue", style=discord.ButtonStyle.grey)
    async def queue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("Music")
        queue = cog.queues.get(self.guild_id, [])
        current = cog.current_tracks.get(self.guild_id)
        
        description = ""
        if current:
            description += f"**Now Playing:** [{current.title}]({current.url})\n\n"
        
        if not queue:
            description += "*Queue is empty*"
        else:
            for i, track in enumerate(queue[:10], 1):
                description += f"**{i}.** [{track.title}]({track.url}) | `{format_duration(track.duration)}`\n"
        
        embed = create_aesthetic_embed(title="📜 Current Queue", description=description)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {} # guild_id: [tracks]
        self.current_tracks = {} # guild_id: track
        self.loops = {} # guild_id: "off", "single", "queue"

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    async def play_next(self, ctx, guild_id):
        queue = self.get_queue(guild_id)
        loop_mode = self.loops.get(guild_id, "off")
        current_track = self.current_tracks.get(guild_id)

        if loop_mode == "single" and current_track:
            track = await YTDLSource.from_url(current_track.url, loop=self.bot.loop, stream=True, requester=current_track.requester)
        elif not queue:
            self.current_tracks[guild_id] = None
            return
        else:
            track = queue.pop(0)
            if loop_mode == "queue" and current_track:
                new_track = await YTDLSource.from_url(current_track.url, loop=self.bot.loop, stream=True, requester=current_track.requester)
                queue.append(new_track)

        self.current_tracks[guild_id] = track
        vc = ctx.guild.voice_client
        if not vc: return

        vc.play(track, after=lambda e: self.bot.loop.create_task(self.play_next(ctx, guild_id)))
        
        embed = create_now_playing_embed(track)
        view = MusicView(self.bot, guild_id)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="play", description="Play a song from YouTube or a URL")
    async def play(self, ctx, *, query: str):
        if not ctx.author.voice:
            return await ctx.send("You need to be in a voice channel!")

        vc = ctx.guild.voice_client
        if not vc:
            vc = await ctx.author.voice.channel.connect()

        async with ctx.typing():
            try:
                track = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True, requester=ctx.author)
            except Exception as e:
                if "ffmpeg was not found" in str(e).lower():
                    return await ctx.send("❌ **FFmpeg not found!** Please ensure FFmpeg is installed and added to your system PATH.")
                return await ctx.send(f"An error occurred: {str(e)}")

        queue = self.get_queue(ctx.guild.id)
        
        if vc.is_playing() or vc.is_paused():
            queue.append(track)
            embed = create_aesthetic_embed(
                title="✅ Added to Queue",
                description=f"**[{track.title}]({track.url})**",
                thumbnail=track.thumbnail,
                fields=[("Duration", format_duration(track.duration), True), ("Position", str(len(queue)), True)]
            )
            await ctx.send(embed=embed)
        else:
            self.current_tracks[ctx.guild.id] = track
            vc.play(track, after=lambda e: self.bot.loop.create_task(self.play_next(ctx, ctx.guild.id)))
            embed = create_now_playing_embed(track)
            view = MusicView(self.bot, ctx.guild.id)
            await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="skip", description="Skip the current song")
    async def skip(self, ctx):
        vc = ctx.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await ctx.send("Skipped the song!")
        else:
            await ctx.send("Nothing is playing!")

    @commands.hybrid_command(name="queue", description="View the current queue")
    async def queue(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        current = self.current_tracks.get(ctx.guild.id)
        
        description = ""
        if current:
            description += f"**Now Playing:** [{current.title}]({current.url})\n\n"
        
        if not queue:
            description += "*Queue is empty*"
        else:
            for i, track in enumerate(queue[:10], 1):
                description += f"**{i}.** [{track.title}]({track.url}) | `{format_duration(track.duration)}`\n"
        
        embed = create_aesthetic_embed(title="📜 Current Queue", description=description)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="loop", description="Toggle loop mode")
    async def loop(self, ctx, mode: str = "off"):
        if mode not in ["off", "single", "queue"]:
            return await ctx.send("Invalid mode! Choose from: `off`, `single`, `queue`")
        self.loops[ctx.guild.id] = mode
        await ctx.send(f"Loop mode set to: `{mode}`")

    @commands.hybrid_command(name="shuffle", description="Shuffle the current queue")
    async def shuffle(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            return await ctx.send("The queue is empty!")
        random.shuffle(queue)
        await ctx.send("🔀 Shuffled the queue!")

    @commands.hybrid_command(name="volume", description="Change the playback volume")
    async def volume(self, ctx, volume: int):
        vc = ctx.guild.voice_client
        if not vc or not vc.source:
            return await ctx.send("Nothing is playing!")
        if 0 <= volume <= 100:
            vc.source.volume = volume / 100
            await ctx.send(f"🔊 Volume set to `{volume}%`")
        else:
            await ctx.send("Volume must be between 0 and 100.")

    @commands.hybrid_command(name="lyrics", description="Search for lyrics")
    async def lyrics(self, ctx, *, query: str = None):
        if not query:
            current = self.current_tracks.get(ctx.guild.id)
            if not current:
                return await ctx.send("Nothing is playing and no query provided.")
            query = current.title
        
        async with ctx.typing():
            lyrics = await get_lyrics(query)
            embed = create_aesthetic_embed(title=f"📜 Lyrics: {query}", description=lyrics[:4000])
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="leave", description="Stop and disconnect the bot")
    async def leave(self, ctx):
        vc = ctx.guild.voice_client
        if vc:
            await vc.disconnect()
            self.queues[ctx.guild.id] = []
            await ctx.send("Disconnected!")
        else:
            await ctx.send("I'm not in a voice channel!")

async def setup(bot):
    await bot.add_cog(Music(bot))
