"""
This cog is for the bot to interact with twitter.
"""
from discord.ext import commands
from tweepy import OAuthHandler
from tweepy import API
import wget
import settings
import discord
import os
from cogs.adminCog import not_banned


class Twitter(commands.Cog):
    """
    Twitter cog for the bot
    """

    def __init__(self, client):
        """
        Constructor for the twitter cog
        :param client: Client object
        :return: None
        """
        self.client = client

        twitter_config = settings.info_json.get("twitter", {})
        required = ("apikey", "apisecret", "accesstoken", "accesstokensecret")
        missing = [key for key in required if not twitter_config.get(key)]
        if missing:
            raise RuntimeError(f"config is missing twitter.{', twitter.'.join(missing)}, "
                               f"the twitter commands are unavailable")

        self.auth = OAuthHandler(twitter_config["apikey"], twitter_config["apisecret"])
        self.auth.set_access_token(twitter_config["accesstoken"], twitter_config["accesstokensecret"])
        self.auth_api = API(self.auth)

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Logs that the cog was loaded properly
        :return: None
        """
        settings.logger.info(f"twit cog ready!")

    @commands.command(brief="Retrieves the most recent post from factbot.")
    @not_banned()
    async def factbot(self, ctx):
        """
        gets the most recently tweeted image from the Twitter account @factbot1
        :param ctx: Context of the command
        :return: None
        """
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
        """
        get the most recently tweeted image from give username
        :param username: username to get the image from
        :param save_as: filename to save the image as
        :return: None
        """
        try:
            tweets = self.auth_api.user_timeline(screen_name=username, count=1, include_rts=False,
                                                 exclude_replies=True)
            tmp = []
            tweets_for_csv = [tweet.text for tweet in tweets]  # CSV file created
            for j in tweets_for_csv:
                # Appending tweets to the empty array tmp
                tmp.append(j)
            settings.logger.debug(f"Tweet data: {tmp}")
            media_files = set()
            for status in tweets:
                media = status.entities.get('media', [])
                if len(media) > 0:
                    media_files.add(media[0]['media_url'])
            for media_file in media_files:
                try:
                    if save_as.endswith(".jpg") or save_as.endswith(".png"):
                        wget.download(media_file, save_as)
                    else:
                        wget.download(media_file, "image.jpg")
                except Exception as e:
                    settings.logger.error(f"Download failed: {e}")
        except Exception as e:
            settings.logger.error(f"Twitter API error: {e}")


async def setup(client):
    """
    Setup function for the twitter cog
    :param client: Client object
    :return: None:
    """
    await client.add_cog(Twitter(client))
