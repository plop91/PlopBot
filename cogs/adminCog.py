from discord.ext import commands
import settings


class admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        settings.logger.info(f"admin cog ready!")

    @commands.command(brief="Admin only command: Turn the bot off.")
    async def kill(self, ctx):
        settings.logger.info(f"kill from {ctx.author}!")
        if str(ctx.message.channel) in settings.json["command_channels"]:
            await self.client.logout()
            exit(0)


def setup(client):
    client.add_cog(admin(client))
