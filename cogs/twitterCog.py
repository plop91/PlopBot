import discord
from discord.ext import commands
import json
import os
from tools.twitter.twitterTool import twitter


def readJson():
    with open("info.json") as f:
        data = json.load(f)
        f.close()
        return data


twit = twitter()

info = readJson()


class twitter(commands.Cog):

    def __init__(self, client, info, twit):
        self.client = client
        self.info = info
        self.twitter = twit

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""twitter cog ready!""")

    @commands.command()
    async def factbot(self, ctx):
        await self.twitter.get_last_tweet_image("@factbot1", "factbot.jpg")
        if os.path.exists("factbot.jpg"):
            await ctx.message.channel.send(file=discord.File('factbot.jpg'))
            os.remove("factbot.jpg")
        else:
            await ctx.message.channel.send("could not get new image for some reason.")



def setup(client):
    client.add_cog(twitter(client, info, twit))
