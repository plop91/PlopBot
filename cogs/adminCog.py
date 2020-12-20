from discord.ext import commands
import settings
import datetime


class admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""{datetime.datetime.now()}: admin cog ready!""")

    @commands.command(brief="Admin only command: Turn the bot off.")
    async def kill(self, ctx):
        print(f"""{datetime.datetime.now()}: kill from {ctx.author}""")
        if str(ctx.message.channel) in settings.json["command_channels"]:
            await self.client.logout()
            exit(0)


def setup(client):
    client.add_cog(admin(client))
