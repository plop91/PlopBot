import discord
from discord.ext import commands
import os
from tools.twitter.twitterTool import twitter
from tools.basicTools import readJson

twitter_tool = twitter()

json_name = "info.json"
json = readJson(json_name)


class twitter(commands.Cog):

    def __init__(self, client, info, twit):
        self.client = client
        self.info = info
        self.twitter = twit

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""twitter cog ready!""")

    @commands.command()
    async def getInfo(self, ctx, names):
        json_dump = self.twitter.getInfo(str(names))
        file = discord.File(json_dump, "dump.json")
        await ctx.message.channel.send(file=file)

    @commands.command()
    async def factbot(self, ctx, filename="factbot.jpg"):
        await self.twitter.get_last_tweet_image("@factbot1", save_as=filename)
        channel = ctx.message.channel
        if os.path.exists(filename):
            await channel.send(file=discord.File(filename))
            os.remove(filename)
            await ctx.message.delete()
        else:
            await channel.send("could not get new image for some reason / shits not working cuz")
            await ctx.message.delete()


def setup(client):
    client.add_cog(twitter(client, json, twitter_tool))
