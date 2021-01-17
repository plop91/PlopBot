from discord.ext import commands
from discord.errors import ClientException
from discord.utils import get
import os
import random
import youtube_dl
import discord
import ffmpeg
import shutil
import settings

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': './youtube.mp3',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}


class audio(commands.Cog):
    volume = 0.7
    queues = {}

    def __init__(self, client):
        self.client = client

    # Logs that the cog was loaded properly
    @commands.Cog.listener()
    async def on_ready(self):
        settings.logger.info(f"audio cog ready!")

    # This listener is to facilitate the ability to download an mp3 for use in the soundboard.
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
                            shutil.copy(f"./soundboard/raw/{filename}", f"./soundboard/{filename}")

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

        # noinspection PyBroadException
        try:
            voice = get(self.client.voice_clients, guild=ctx.guild)

            if filename == "random":
                sounds = []
                for file in os.listdir("soundboard"):
                    if file.endswith(".mp3"):
                        sounds.append(file)
                voice.play(discord.FFmpegPCMAudio(source=f"soundboard/{random.choice(sounds)}"))

            else:
                if os.path.exists(f"soundboard/{filename.lower().strip()}.mp3"):
                    voice.play(discord.FFmpegPCMAudio(source=f"soundboard/{filename.lower().strip()}.mp3"))
                    voice.source = discord.PCMVolumeTransformer(voice.source)
                    voice.source.volume = int(self.volume)
                else:
                    await ctx.send("Clip with that name does not exist")
            await ctx.message.delete()

        except AttributeError as e:
            settings.logger.info(f"Attribute Error:")
            settings.logger.info(e)
            await ctx.send(str(ctx.author.name) + " you are not in a channel.")
            await ctx.message.delete()

        except PermissionError as e:
            settings.logger.warning(f"Permission Error:")
            settings.logger.warning(e)
            await ctx.send("Permission error - let ian know if you see this")

        except ClientException as e:
            settings.logger.warning(f"Client Exception:")
            settings.logger.warning(e)
            await ctx.send("The bot is not in the voice channel use '.join' or '.j' to make the bot join.")
            await ctx.message.delete()

        except Exception as e:
            settings.logger.warning(f"unknown exception")
            settings.logger.warning(e)
            await ctx.send("unknown error - let a admin know if you see this")

    # Plays the audio of the provided youtube link.
    @commands.command(pass_context=True, aliases=['yt', 'YOUTUBE', 'YT'],
                      brief="Plays the youtube clip at the url in the argument. alt command = 'yt'",
                      description="Makes the bot play a youtube videos audio. For example if you wanted to play the "
                                  "youtube video at 'https://www.youtube.com/watch?v=1234' you would enter '.youtube "
                                  "https://www.youtube.com/watch?v=1234'/'.yt https://www.youtube.com/watch?v=1234'")
    async def youtube(self, ctx, url):
        try:
            song_there = os.path.isfile("youtube.mp3")

            if song_there:
                os.remove("youtube.mp3")
        except PermissionError:
            settings.logger.info(f"Trying to delete song file, but it's being played")
            await ctx.message.delete()
            return

        voice = get(self.client.voice_clients, guild=ctx.guild)

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            settings.logger.info(f"Downloading audio now :: {url}")
            ydl.download([url])

        voice.play(discord.FFmpegPCMAudio("youtube.mp3"))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = self.volume

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
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")
        volume_adjusted = volume / 100
        self.volume = volume_adjusted
        settings.logger.info(f"volume changed to {volume_adjusted} by {ctx.author}")
        await ctx.send(f"Changed volume to {volume}%")

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


def setup(client):
    client.add_cog(audio(client))
