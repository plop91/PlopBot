from asyncio import sleep

import discord
from discord.ext import commands
from discord.utils import get
from tools.basicTools import readJson
import youtube_dl
import os

info = readJson("info.json")


class audio(commands.Cog):

    def __init__(self, client, info):
        self.client = client
        self.info = info

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""audio cog ready!""")

    """
    @commands.command(pass_context=True, aliases=['j'])
    async def join(self, ctx):
        global voice
        channel = ctx.message.author.voice.channel
        voice = get(self.client.voice_clienrs, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
    """

    @commands.command(pass_context=True, aliases=['p'])
    async def play(self, ctx):
        # Gets voice channel of message author
        voice_channel = ctx.author.voice.channel

        if voice_channel is not None:
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio(source="soundboard/china.mp3"))
            vc.source = discord.PCMVolumeTransformer(vc.source)
            vc.source.volume = 0.7
            while vc.is_playing():
                continue
            await vc.disconnect()
        else:
            await ctx.send(str(ctx.author.name) + "is not in a channel.")
        # Delete command after the audio is done playing.
        await ctx.message.delete()

    @commands.command()
    async def youtube(self, ctx, url):
        # Gets voice channel of message author
        voice_channel = ctx.author.voice.channel

        if voice_channel is not None:

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                print("Downloading audio now\n")
                ydl.download([url])

            for file in os.listdir("./"):
                if file.endswith(".mp3"):
                    name = file
                    print(f"Renamed File: {file}\n")
                    os.rename(file, "song.mp3")

            vc = await voice_channel.connect()

            vc.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: print("Song done!"))
            vc.source = discord.PCMVolumeTransformer(vc.source)
            vc.source.volume = 0.07

            while vc.is_playing():
                continue
            await vc.disconnect()
        else:
            await ctx.send(str(ctx.author.name) + "is not in a channel.")
        # Delete command after the audio is done playing.
        await ctx.message.delete()


def setup(client):
    client.add_cog(audio(client, info))
