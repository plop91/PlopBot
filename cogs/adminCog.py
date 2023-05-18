from discord.ext import commands
import settings


class Admin(commands.Cog):
    """
    Admin cog for the bot
    """

    def __init__(self, client):
        """
        Constructor for the admin cog
        :arg client: client object
        """
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Logs that the cog was loaded properly
        :return: None
        """
        settings.logger.info(f"admin cog ready!")

    @commands.command(brief="Admin only command: provide current git commit hash")
    async def hash(self, ctx):
        """
        provide current git commit hash
        :arg ctx: context of the command
        :return: None
        """
        pass

    @commands.command(brief="Admin only command: provide current version")
    async def version(self, ctx):
        """
        provide current version of the bot
        :arg ctx: context of the command
        :return: None
        """
        pass

    @commands.command(brief="Admin only command: Turn the bot off.")
    async def kill(self, ctx):
        """
        Preforms a shutdown of the bot
        :arg ctx: context of the command
        :return: None
        """
        # try to gracefully shut down the bot
        # noinspection PyBroadException
        try:
            if str(ctx.author) in settings.info_json["admins"]:
                settings.logger.info(f"kill from {ctx.author}!")
                if str(ctx.message.channel) in settings.info_json["command_channels"]:
                    await self.client.logout()
            else:
                await ctx.channel.send(ctx.author)
                await ctx.channel.send(settings.info_json["admins"])
                await ctx.channel.send("you are not an admin")
        # if the bot fails to log out kill it
        except Exception:
            exit(1)

    @commands.command(brief="Admin only command: Restart the bot.")
    async def restart(self, ctx):
        """
        Preforms a restart of the bot
        :arg ctx: context of the command
        :return: None
        """
        # try to gracefully shut down the bot
        # noinspection PyBroadException
        try:
            if str(ctx.author) in settings.info_json["admins"]:
                settings.logger.info(f"restart from {ctx.author}!")
                if str(ctx.message.channel) in settings.info_json["command_channels"]:
                    await self.client.logout()
                    await self.client.start(settings.info_json["token"])
            else:
                await ctx.channel.send(ctx.author)
                await ctx.channel.send(settings.info_json["admins"])
                await ctx.channel.send("you are not an admin")
        # if the bot fails to log out kill it
        except Exception:
            exit(1)


async def setup(client):
    """
    Adds the cog to the bot
    :arg client: client object
    :return: None
    """
    await client.add_cog(Admin(client))
