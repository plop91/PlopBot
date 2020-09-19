import os
import random
import youtube_dl
import discord
from discord.ext import commands
from discord.errors import ClientException
from discord.utils import get
from tools.basicTools import readJson

json = readJson("info.json")


class audio(commands.Cog):

    def __init__(self, client, info):
        self.client = client
        self.info = info

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""audio cog ready!""")

    # This listener is to facilitate the ability to download an mp3 for use in the soundboard.
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith(".mp3"):
                    if os.path.exists(f"./soundboard/{attachment.filename.lower().replace(' ', '')}"):
                        print(f"{message.author} tried to add a mp3 file: {attachment} but a file with that name already exists.")
                        await message.channel.send("A clip with that name already exists please rename it to upload.")
                    else:
                        print(f"{message.author} added a mp3 file: {attachment}")
                        await message.channel.send(
                            f"The audio is being downloaded and should be ready shortly the name of the clip will be: "
                            f"{attachment.filename.lower().replace(' ', '').replace('.mp3', '')}")
                        await attachment.save(f"./soundboard/{attachment.filename.lower().replace(' ', '')}")

    @commands.command(pass_context=True, aliases=['j', 'JOIN'],
                      brief="Make the bot Join the voice server. alt command = 'j'",
                      description="Makes the bot join the voice server this is required to use the play, youtube, "
                                  "leave, pause and resume functions")
    async def join(self, ctx):
        channel = ctx.message.author.voice.channel
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()

        await voice.disconnect()

        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            await channel.connect()
            print(f"The bot has connected to {channel}\n")

        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['l', 'LEAVE'],
                      brief="Make the bot leave the voice server. alt command = 'l'",
                      description="Makes the bot leave the voice server.")
    async def leave(self, ctx):
        channel = ctx.message.author.voice.channel
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            print(f"The bot has left {channel}")
        else:
            print("Bot was told to leave voice channel, but was not in one")
            await ctx.send("Don't think I am in a voice channel")

        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['PAUSE'], brief="Pause everything the bot is playing",
                      description="Makes the bot pause anything that it is playing.")
    async def pause(self, ctx):

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

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            voice.stop()
        else:
            await ctx.send("No music playing dum dum")

        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['p', 'PLAY', 'P'],
                      brief="Plays a clip with the same name as the argument. alt command = 'p'",
                      description="Makes the bot play one of the soundboard files. For example if you wanted to play "
                                  "a file named hammer you would enter '.play hammer'/'.p hammer'")
    async def play(self, ctx, filename=None):

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
                print(random.choice(sounds))
                voice.play(discord.FFmpegPCMAudio(source=f"soundboard/{random.choice(sounds)}"))

            else:
                voice.play(discord.FFmpegPCMAudio(source=f"soundboard/{filename.lower().strip()}.mp3"))
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = 0.7

            await ctx.message.delete()
        except AttributeError:
            await ctx.send(str(ctx.author.name) + " you are not in a channel.")
            await ctx.message.delete()
        except PermissionError as e:
            print(e)
            await ctx.send("Permission error - let ian know if you see this")
        except ClientException:
            await ctx.send("The bot is not in the voice channel use '.join' or '.j' to make the bot join.")
            await ctx.message.delete()
        except Exception as e:
            print(e)
            await ctx.send("unknown error - let ian know if you see this")

    @commands.command(pass_context=True, aliases=['yt', 'YOUTUBE'],
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
            print("Trying to delete song file, but it's being played")
            await ctx.message.delete()
            return

        voice = get(self.client.voice_clients, guild=ctx.guild)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': './youtube.mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading audio now\n")
            ydl.download([url])

        voice.play(discord.FFmpegPCMAudio("youtube.mp3"))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.7


def setup(client):
    client.add_cog(audio(client, json))
