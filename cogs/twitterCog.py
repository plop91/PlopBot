import discord
from discord.ext import commands
import json
import os
from tools.twitter.twitterTool import twitter

try:
    from tools.GoogleAPi.imageRecognition import imageclassifier

    classify = True
except ImportError:
    classify = False


def readJson():
    with open("info.json") as f:
        data = json.load(f)
        f.close()
        return data


twit = twitter()

info = readJson()

if classify is True:
    try:
        classifier = imageclassifier()
    except:
        classify = False


class twitter(commands.Cog):

    def __init__(self, client, info, twit, classifier=None):
        self.client = client
        self.info = info
        self.twitter = twit
        if classifier is not None:
            self.classifier = classifier

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
            if classify:
                with open(filename) as f:
                    labels = await self.classifier.classify(f)
                    f.close()
                    if info:
                        for label in labels:
                            print(label.description)
                            # discord.utils.get(guild.TextChannel, name='bot_commands').send(label.description)
            os.remove(filename)
            await ctx.message.delete()
        else:
            await channel.send("could not get new image for some reason / shits not working cuz")
            await ctx.message.delete()


def setup(client):
    if classify is True:
        client.add_cog(twitter(client, info, twit, classifier=classifier))
    elif classify is False:
        client.add_cog(twitter(client, info, twit))
