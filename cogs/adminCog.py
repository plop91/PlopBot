from discord.ext import commands
import settings


class admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Logs that the cog was loaded properly
    @commands.Cog.listener()
    async def on_ready(self):
        settings.logger.info(f"admin cog ready!")

    # Preforms a shutdown of the bot
    @commands.command(brief="Admin only command: Turn the bot off.")
    async def kill(self, ctx):
        # try to gracefully shutdown the bot
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
        # if the bot fails to logout kill it
        except Exception:
            exit(1)

    # Preforms a restart of the bot
    @commands.command(brief="Admin only command: Restart the bot.")
    async def restart(self, ctx):
        # try to gracefully shutdown the bot
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
        # if the bot fails to logout kill it
        except Exception:
            exit(1)


async def setup(client):
    await client.add_cog(admin(client))
