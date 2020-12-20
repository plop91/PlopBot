from discord.ext import commands
from utility.twit import twit
import settings
import discord
import os


class twitter(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.twitter = twit()

    @commands.Cog.listener()
    async def on_ready(self):
        settings.logger.info(f"twit cog ready!")

    @commands.command(brief="Dumps info about the twit account in the argument.")
    async def getInfo(self, ctx, names):
        json_dump = self.twitter.getInfo(str(names))
        file = discord.File(json_dump, "dump.json")
        settings.logger.info(f"get info : {ctx.author}")
        await ctx.message.channel.send(file=file)

    @commands.command(brief="Retrieves the most recent post from factbot.")
    async def factbot(self, ctx, filename="factbot.jpg"):
        settings.logger.info(f"factbot : {ctx.author}")
        await self.twitter.get_last_tweet_image("@factbot1", save_as=filename)
        channel = ctx.message.channel
        if os.path.exists(filename):
            await channel.send(file=discord.File(filename))
            os.remove(filename)
            await ctx.message.delete()
        else:
            settings.logger.info(f"Could not get new image.")
            settings.logger.debug(f"Factbot may be down! check for updates?")
            await channel.send("Could not get new image.")
            await ctx.message.delete()


def setup(client):
    client.add_cog(twitter(client))
