from discord.ext import commands, tasks
from discord.errors import ClientException
from discord.utils import get
import asyncio
import os
import random
import youtube_dl
import discord
import ffmpeg
import shutil
import settings

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'youtube/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


def clean_youtube():
    settings.logger.info(f"cleaning youtube folder!")
    for f in os.listdir("youtube"):
        os.remove(os.path.join("youtube", f))


async def play_clip(client, filename):
    try:
        if filename == "random":
            sounds = []
            for file in os.listdir("soundboard"):
                if file.endswith(".mp3"):
                    sounds.append(file)
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(source=f"soundboard/{random.choice(sounds)}"))
        else:
            if os.path.exists(f"soundboard/{filename.lower().strip()}.mp3"):
                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(source=f"soundboard/{filename.lower().strip()}.mp3"))
            else:
                return
        client.play(source)

    except AttributeError as e:
        settings.logger.info(f"Attribute Error:")
        settings.logger.info(e)

    except PermissionError as e:
        settings.logger.warning(f"Permission Error:")
        settings.logger.warning(e)

    except ClientException as e:
        settings.logger.warning(f"Client Exception:")
        settings.logger.warning(e)

    except Exception as e:
        settings.logger.warning(f"unknown exception")
        settings.logger.warning(e)


class audio(commands.Cog):
    volume = 0.7

    def __init__(self, client):
        self.client = client
        self.maintenance.start()

    # Logs that the cog was loaded properly and empties the youtube folder.
    @commands.Cog.listener()
    async def on_ready(self):
        settings.logger.info(f"audio cog ready!")

    # Logs the bot turning off
    @commands.Cog.listener()
    async def on_disconnect(self):
        clean_youtube()

    # This listener is to facilitate the ability to download an mp3 for use in the soundboard as well as interprets
    # webhooks from my website.
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith(".mp3"):
                    if os.path.exists(f"./soundboard/{attachment.filename.lower().replace(' ', '')}"):
                        settings.logger.info(
                            f"{message.author} tried to add a mp3 file: {attachment} but a file with that name "
                            f"already exists.")
                        await message.channel.send("A clip with that name already exists please rename it to upload.")
                    elif os.path.exists(f"./soundboard/raw/{attachment.filename.lower().replace(' ', '')}"):
                        settings.logger.info(
                            f"{message.author} tried to add a mp3 file: {attachment} but a file with that name "
                            f"already exists in raw clips.")
                        await message.channel.send("A clip with that name has already been uploaded and is waiting "
                                                   "for admin approval. Notify an admin to resolve.")
                    else:
                        filename = attachment.filename.lower().replace(' ', '').replace('_', '')
                        settings.logger.info(f"{message.author} added a mp3 file: {attachment}")
                        await message.channel.send(
                            f"The audio is being downloaded and should be ready shortly the name of the clip will be: "
                            f"{filename.replace('.mp3', '')}")
                        await attachment.save(f"./soundboard/raw/{filename}")
                        audio_json = ffmpeg.probe(f"./soundboard/raw/{filename}")

                        # the jon rule - if the clip is too long i have to review it
                        if float(audio_json['streams'][0]['duration']) >= 60:
                            await message.channel.send("The clip is longer than a minute and will need to be reviewed "
                                                       "before it can be played, thank jon for this feature.")
                        else:
                            try:
                                settings.soundboard_db.add_db_entry(filename.lower(),
                                                                    filename.replace(".mp3", "").lower())
                                shutil.copy(f"./soundboard/raw/{filename}", f"./soundboard/{filename}")
                            except ValueError:
                                await message.channel.send("A file with that name already existed in the database, "
                                                           "contact an admin!")
                                settings.logger.warning("a file with the same name exists in the database but not on "
                                                        "the server")

        else:
            data = message.content.split(':')
            if data[0] == "www.sodersjerna.com":
                member = discord.utils.get(message.guild.members, name=data[1])
                if member is not None and member.voice is not None:
                    for client in self.client.voice_clients:
                        if client.channel.id == member.voice.channel.id:
                            if data[2] == "stop":
                                if client.is_playing():
                                    client.stop()
                            elif data[2] == "pause":
                                if client.is_playing():
                                    client.pause()
                            elif data[2] == "resume":
                                if client.is_paused():
                                    client.resume()
                            elif data[2] == "play":
                                await play_clip(client, data[3])
                await message.delete()

    # Plays an mp3 from the library of downloaded mp3's
    @commands.command(pass_context=True, aliases=['p', 'PLAY', 'P'],
                      brief="Plays a clip with the same name as the argument. alt command = 'p'",
                      description="Makes the bot play one of the soundboard files. For example if you wanted to play "
                                  "a file named hammer you would enter '.play hammer'/'.p hammer'")
    async def play(self, ctx, filename=None):

        settings.logger.info(f"play from {ctx.author} :{filename}")

        if filename is None:
            embed_var = discord.Embed(title="Soundboard files", description="type '.play ' followed by a name to play "
                                                                            "file", color=0x00ff00)
            s = ""
            for file in os.listdir("soundboard"):
                if file.endswith(".mp3"):
                    temp = file.strip().replace(".mp3", "").lower()
                    if len(s) + len(temp) >= 1024:
                        embed_var.add_field(name="play from a filename:", value=s, inline=False)
                        s = ""
                    s += temp + ", "

            embed_var.add_field(name="play from a filename:", value=s, inline=False)

            embed_var.add_field(name="play a random file:", value="random", inline=False)

            await ctx.channel.send(embed=embed_var)
            await ctx.message.delete()

            return

        await play_clip(ctx.voice_client, filename)
        await ctx.message.delete()

    # Downloads and plays the audio of the provided youtube link. Plays from a url (almost anything youtube_dl supports)
    @commands.command(pass_context=True, aliases=['yt', 'YOUTUBE', 'YT'],
                      brief="Plays the youtube clip at the url in the argument. alt command = 'yt'",
                      description="Makes the bot play a youtube videos audio. For example if you wanted to play the "
                                  "youtube video at 'https://www.youtube.com/watch?v=1234' you would enter '.youtube "
                                  "https://www.youtube.com/watch?v=1234'/'.yt https://www.youtube.com/watch?v=1234'")
    async def youtube(self, ctx, *, url):
        settings.logger.info(f"youtube from {ctx.author} :{url}")
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.client.loop)
            ctx.voice_client.play(player)
        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=[],
                      brief="Streams from a url (same as yt, but doesn't pre-download)",
                      description="")
    async def stream(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.client.loop, stream=True)
            ctx.voice_client.play(player)
        await ctx.message.delete()

    # Forces the bot to leave whatever voice channel it is in.
    @commands.command(pass_context=True, aliases=['l', 'LEAVE', 'L'],
                      brief="Make the bot leave the voice server. alt command = 'l'",
                      description="Makes the bot leave the voice server.")
    async def leave(self, ctx):
        settings.logger.info(f"leave from {ctx.author}")

        channel = ctx.message.author.voice.channel
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            settings.logger.info(f"The bot has left {channel}")
        else:
            settings.logger.info(f"Bot was told to leave voice channel, but was not in one!")
            await ctx.send("Don't think I am in a voice channel")

        await ctx.message.delete()

    # Pauses whatever the bot is playing
    @commands.command(pass_context=True, aliases=['PAUSE'], brief="Pause everything the bot is playing",
                      description="Makes the bot pause anything that it is playing.")
    async def pause(self, ctx):
        settings.logger.info(f"pause from {ctx.author}")

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            voice.pause()
        else:
            await ctx.send("No music playing dum dum")

        await ctx.message.delete()

    # Resumes playing if the bot is paused
    @commands.command(pass_context=True, aliases=['r', 'RESUME', 'R'],
                      brief="Resume playing paused Music. alt command = 'r'",
                      description="Makes the bot resume playing any paused audio.")
    async def resume(self, ctx):
        settings.logger.info(f"resume from {ctx.author}")

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_paused():
            voice.resume()
        else:
            await ctx.send("No music paused dum dum")

        await ctx.message.delete()

    # Stops playing whatever is playing
    @commands.command(pass_context=True, aliases=['s', 'STOP', 'S'],
                      brief="Stop any Music the bot is playing or has paused. alt "
                            "command = 's'", description="Makes the bot stop playing "
                                                         "any audio and forget what "
                                                         "it was playing and when it "
                                                         "stopped.")
    async def stop(self, ctx):
        settings.logger.info(f"stop from {ctx.author}")

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            voice.stop()
        else:
            await ctx.send("No music playing dum dum")

        await ctx.message.delete()

    # Change the volume the bot plays back at
    @commands.command(pass_context=True, aliases=['v', 'VOLUME', 'V', 'vol'], brief="changes the volume of the bot",
                      description="Changes the volume of the bot.")
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        settings.logger.info(f"volume changed to {volume} by {ctx.author}")
        await ctx.message.delete()
        await ctx.send(f"Changed volume to {volume}")

    # Verifies the bot is in a voice channel before it tries to play something new.
    @play.before_invoke
    @youtube.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

    # changes the bot to a randomly provided status.
    @tasks.loop(seconds=0, minutes=0, hours=24)
    async def maintenance(self):
        clean_youtube()
        settings.soundboard_db.verify_db()


def setup(client):
    client.add_cog(audio(client))
