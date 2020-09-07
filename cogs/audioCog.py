import discord
from discord.ext import commands, tasks
from tools.basicTools import readJson
import os

# from discord.utils import get
# import youtube_dl

json = readJson("info.json")


class audio(commands.Cog):
    vc = None

    def __init__(self, client, info):
        self.client = client
        self.info = info
        self.autoDisconnect.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""audio cog ready!""")

    @commands.command(aliases=['p'])
    async def play(self, ctx, filename=None):

        if filename is None:
            embed_var = discord.Embed(title="Soundboard files", description="type '.play ' followed by a name to play "
                                                                            "file", color=0x00ff00)
            for file in os.listdir("soundboard"):
                if file.endswith(".mp3"):
                    s = file.strip(".mp3").lower()
                    embed_var.add_field(name=s, value="play this file", inline=False)

            await ctx.channel.send(embed=embed_var)
            await ctx.message.delete()
            return
        try:
            if self.vc is None:
                voice_channel = ctx.author.voice.channel
                if voice_channel is not None:
                    self.vc = await voice_channel.connect()
                else:
                    await ctx.send(str(ctx.author.name) + "is not in a channel.")
                    return

            self.vc.play(discord.FFmpegPCMAudio(source=f"soundboard/{filename.lower()}.mp3"))
            self.vc.source = discord.PCMVolumeTransformer(self.vc.source)
            self.vc.source.volume = 0.7

            await ctx.message.delete()
        except AttributeError:
            await ctx.send(str(ctx.author.name) + " you are not in a channel.")

    @commands.command()
    async def stop(self, ctx):
        if self.vc is not None:
            await self.vc.disconnect()
            self.vc = None
            await ctx.message.delete()

    @tasks.loop(seconds=1, minutes=0, hours=0)
    async def autoDisconnect(self):
        if self.vc is not None:
            if self.vc.is_connected():
                if not self.vc.is_playing():
                    self.vc.disconnect()
                    self.vc = None

    # @commands.command()
    # async def youtube(self, ctx, url):
    #     # Gets voice channel of message author
    #     voice_channel = ctx.author.voice.channel
    #
    #     if voice_channel is not None:
    #
    #         ydl_opts = {
    #             'format': 'bestaudio/best',
    #             'postprocessors': [{
    #                 'key': 'FFmpegExtractAudio',
    #                 'preferredcodec': 'mp3',
    #                 'preferredquality': '192',
    #             }],
    #         }
    #
    #         with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    #             print("Downloading audio now\n")
    #             ydl.download([url])
    #
    #         for file in os.listdir("./"):
    #             if file.endswith(".mp3"):
    #                 name = file
    #                 print(f"Renamed File: {file}\n")
    #                 os.rename(file, "song.mp3")
    #
    #         vc = await voice_channel.connect()
    #
    #         vc.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: print("Song done!"))
    #         vc.source = discord.PCMVolumeTransformer(vc.source)
    #         vc.source.volume = 0.07
    #
    #         while vc.is_playing():
    #             continue
    #         await vc.disconnect()
    #     else:
    #         await ctx.send(str(ctx.author.name) + "is not in a channel.")
    #     # Delete command after the audio is done playing.
    #     await ctx.message.delete()


def setup(client):
    client.add_cog(audio(client, json))
