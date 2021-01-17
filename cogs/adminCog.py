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
        try:
            if ctx.author in settings.json["admins"]:
                settings.logger.info(f"kill from {ctx.author}!")
                if str(ctx.message.channel) in settings.json["command_channels"]:
                    await self.client.logout()
                    exit(0)
        # if the bot fails to logout kill it
        except Exception:
            exit(1)


def setup(client):
    client.add_cog(admin(client))
