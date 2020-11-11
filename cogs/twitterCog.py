from discord.ext import commands
from utility.twitter import twitter
import settings
import discord
import os
import datetime

twitter_tool = twitter()


class twitter(commands.Cog):

    def __init__(self, client, info, twit):
        self.client = client
        self.info = info
        self.twitter = twit

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""{datetime.datetime.now()}: twitter cog ready!""")

    @commands.command(brief="Dumps info about the twitter account in the argument.")
    async def getInfo(self, ctx, names):
        json_dump = self.twitter.getInfo(str(names))
        file = discord.File(json_dump, "dump.json")
        await ctx.message.channel.send(file=file)

    @commands.command(brief="Retrieves the most recent post from factbot.")
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
    client.add_cog(twitter(client, settings.json, twitter_tool))
