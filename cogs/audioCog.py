from discord.ext import commands
from discord.errors import ClientException
from discord.utils import get
import os
import random
import youtube_dl
import discord
import ffmpeg
import shutil
import datetime
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

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""{datetime.datetime.now()}: audio cog ready!""")

    # This listener is to facilitate the ability to download an mp3 for use in the soundboard.
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith(".mp3"):
                    if os.path.exists(f"./soundboard/{attachment.filename.lower().replace(' ', '')}"):
                        print(f"{datetime.datetime.now()}: {message.author} tried to add a mp3 file: {attachment}"
                              f" but a file with that name already exists.")
                        await message.channel.send("A clip with that name already exists please rename it to upload.")
                    elif os.path.exists(f"./soundboard/raw/{attachment.filename.lower().replace(' ', '')}"):
                        print(f"{datetime.datetime.now()}: {message.author} tried to add a mp3 file: {attachment} "
                              f"but a file with that name already exists in raw clips.")
                        await message.channel.send("A clip with that name has already been uploaded and is waiting "
                                                   "for admin approval. Notify an admin to resolve.")
                    else:
                        filename = attachment.filename.lower().replace(' ', '').replace('_', '')
                        print(f"{datetime.datetime.now()}: {message.author} added a mp3 file: {attachment}")
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

    # @commands.command(pass_context=True, aliases=['j', 'JOIN', 'J'],
    #                   brief="Make the bot Join the voice server. alt command = 'j'",
    #                   description="Makes the bot join the voice server this is required to use the play, youtube, "
    #                               "leave, pause and resume functions")
    # async def join(self, ctx):
    #     print(f"""{datetime.datetime.now()}: join from {ctx.author}""")
    #
    #     channel = ctx.message.author.voice.channel
    #     voice = get(self.client.voice_clients, guild=ctx.guild)
    #
    #     if voice and voice.is_connected():
    #         await voice.move_to(channel)
    #     else:
    #         voice = await channel.connect()
    #
    #     await voice.disconnect()
    #
    #     if voice and voice.is_connected():
    #         await voice.move_to(channel)
    #     else:
    #         await channel.connect()
    #         print(f"{datetime.datetime.now()}: The bot has connected to {channel}\n")
    #
    #     await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['p', 'PLAY', 'P'],
                      brief="Plays a clip with the same name as the argument. alt command = 'p'",
                      description="Makes the bot play one of the soundboard files. For example if you wanted to play "
                                  "a file named hammer you would enter '.play hammer'/'.p hammer'")
    async def play(self, ctx, filename=None):
        print(f"""{datetime.datetime.now()}: play from {ctx.author} :{filename}""")

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
                    voice.source.volume = self.volume
                else:
                    await ctx.send("Clip with that name does not exist")
            await ctx.message.delete()

        except AttributeError as e:
            print(f"""{datetime.datetime.now()}:""")
            print(e)
            await ctx.send(str(ctx.author.name) + " you are not in a channel.")
            await ctx.message.delete()

        except PermissionError as e:
            print(f"""{datetime.datetime.now()}:""")
            print(e)
            await ctx.send("Permission error - let ian know if you see this")

        except ClientException as e:
            print(f"""{datetime.datetime.now()}:""")
            print(e)
            await ctx.send("The bot is not in the voice channel use '.join' or '.j' to make the bot join.")
            await ctx.message.delete()

        except Exception as e:
            print(f"""{datetime.datetime.now()}:""")
            print(e)
            await ctx.send("unknown error - let a admin know if you see this")

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
            print(f"{datetime.datetime.now()}: Trying to delete song file, but it's being played")
            await ctx.message.delete()
            return

        voice = get(self.client.voice_clients, guild=ctx.guild)

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print(f"{datetime.datetime.now()}: Downloading audio now :: {url}\n")
            ydl.download([url])

        voice.play(discord.FFmpegPCMAudio("youtube.mp3"))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = self.volume

    @commands.command(pass_context=True, aliases=['l', 'LEAVE', 'L'],
                      brief="Make the bot leave the voice server. alt command = 'l'",
                      description="Makes the bot leave the voice server.")
    async def leave(self, ctx):
        print(f"""{datetime.datetime.now()}: leave from {ctx.author}""")

        channel = ctx.message.author.voice.channel
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            print(f"{datetime.datetime.now()}: The bot has left {channel}")
        else:
            print(f"{datetime.datetime.now()}: Bot was told to leave voice channel, but was not in one")
            await ctx.send("Don't think I am in a voice channel")

        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['PAUSE'], brief="Pause everything the bot is playing",
                      description="Makes the bot pause anything that it is playing.")
    async def pause(self, ctx):
        print(f"""{datetime.datetime.now()}: pause from {ctx.author}""")

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            voice.pause()
        else:
            await ctx.send("No music playing dum dum")

        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['r', 'RESUME', 'R'],
                      brief="Resume playing paused Music. alt command = 'r'",
                      description="Makes the bot resume playing any paused audio.")
    async def resume(self, ctx):
        print(f"""{datetime.datetime.now()}: resume from {ctx.author}""")

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_paused():
            voice.resume()
        else:
            await ctx.send("No music paused dum dum")

        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['s', 'STOP', 'S'],
                      brief="Stop any Music the bot is playing or has paused. alt "
                            "command = 's'", description="Makes the bot stop playing "
                                                         "any audio and forget what "
                                                         "it was playing and when it "
                                                         "stopped.")
    async def stop(self, ctx):
        print(f"""{datetime.datetime.now()}: stop from {ctx.author}""")

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            voice.stop()
        else:
            await ctx.send("No music playing dum dum")

        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['v', 'VOLUME', 'V', 'vol'], brief="changes the volume of the bot",
                      description="Changes the volume of the bot.")
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")
        volume_adjusted = volume / 100
        self.volume = volume_adjusted
        print(f"""{datetime.datetime.now()}: volume changed to {volume_adjusted} by {ctx.author}""")
        await ctx.send(f"Changed volume to {volume}%")

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
