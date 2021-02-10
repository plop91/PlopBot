from discord.ext import commands
from tweepy import OAuthHandler
from tweepy import API
import wget
import settings
from settings import readJson
import discord
import os


class twitter(commands.Cog):

    def __init__(self, client):
        self.client = client

        self.info = readJson("twittertoken.json")
        self.auth = OAuthHandler(self.info["apikey"], self.info["apisecret"])
        self.auth.set_access_token(self.info["accesstoken"], self.info["accesstokensecret"])
        self.auth_api = API(self.auth)

    @commands.Cog.listener()
    async def on_ready(self):
        """Logs that the cog was loaded properly"""
        settings.logger.info(f"twit cog ready!")

    @commands.command(brief="Retrieves the most recent post from factbot.")
    async def factbot(self, ctx):
        """gets the most recently tweeted image from the twitter account @factbot1"""
        filename = "factbot.jpg"
        settings.logger.info(f"factbot : {ctx.author}")
        await self.get_last_tweet_image("@factbot1", save_as=filename)
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

    async def get_last_tweet_image(self, username, save_as="image.jpg"):
        """get the most recently tweeted image from give username"""
        tweets = self.auth_api.user_timeline(screen_name=username, count=1, include_rts=False,
                                             exclude_replies=True)
        tmp = []
        tweets_for_csv = [tweet.text for tweet in tweets]  # CSV file created
        for j in tweets_for_csv:
            # Appending tweets to the empty array tmp
            tmp.append(j)
        print(tmp)
        media_files = set()
        for status in tweets:
            media = status.entities.get('media', [])
            if len(media) > 0:
                media_files.add(media[0]['media_url'])
        for media_file in media_files:
            if save_as.endswith(".jpg") or save_as.endswith(".png"):
                wget.download(media_file, save_as)
            else:
                wget.download(media_file, "image.jpg")


def setup(client):
    client.add_cog(twitter(client))
